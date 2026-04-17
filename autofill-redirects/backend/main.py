from io import BytesIO
from pathlib import Path
import tempfile

import pandas as pd
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Redirect Resolver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_AGENT = "Mozilla/5.0 (compatible; RedirectResolver/1.0)"


def excel_col_name_to_index(col_name: str) -> int:
    col_name = col_name.strip().upper()
    if not col_name.isalpha():
        raise ValueError("Column letters must contain only A-Z.")
    result = 0
    for ch in col_name:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def resolve_column_index(mode: str, value: str, df: pd.DataFrame) -> int:
    if mode == "letter":
        idx = excel_col_name_to_index(value)
        if idx >= len(df.columns):
            raise ValueError(f"Column '{value}' is outside the sheet range.")
        return idx

    target = value.strip()
    for i, col in enumerate(df.columns):
        if str(col).strip() == target:
            return i
    raise ValueError(f"Header '{value}' was not found in the selected sheet.")


def load_dataframe(temp_path: Path, sheet_name: str | None) -> pd.DataFrame:
    read_kwargs = {}
    if sheet_name:
        read_kwargs["sheet_name"] = sheet_name
    return pd.read_excel(temp_path, **read_kwargs)


@app.post("/api/process")
async def process_file(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
    start_row: int = Form(default=2),
    source_mode: str = Form(default="letter"),
    source_value: str = Form(default="D"),
    output_mode: str = Form(default="letter"),
    output_value: str = Form(default="E"),
    timeout: int = Form(default=15),
):
    if start_row < 1:
        raise HTTPException(status_code=400, detail="Start row must be 1 or greater.")

    suffix = Path(file.filename or "input.xlsx").suffix.lower() or ".xlsx"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        temp_path = Path(tmp.name)

    try:
        df = load_dataframe(temp_path, sheet_name)
        src_idx = resolve_column_index(source_mode, source_value, df)
        out_idx = resolve_column_index(output_mode, output_value, df)

        output_col = df.columns[out_idx]

        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        for row_idx in range(start_row - 1, len(df)):
            raw_url = df.iat[row_idx, src_idx]
            if pd.isna(raw_url) or str(raw_url).strip() == "":
                continue

            url = str(raw_url).strip()
            try:
                response = session.get(url, allow_redirects=True, timeout=timeout)
                final_url = response.url
            except Exception as exc:
                final_url = f"ERROR: {exc}"

            df.at[row_idx, output_col] = final_url

        output = BytesIO()
        output_filename = f"{Path(file.filename or 'redirects').stem}_completed.xlsx"
        df.to_excel(output, index=False)
        output.seek(0)

        headers = {"Content-Disposition": f'attachment; filename="{output_filename}"'}
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
