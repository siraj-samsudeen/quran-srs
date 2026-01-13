from fasthtml.common import *
from app.common_function import create_app_with_auth
from app.admin_model import *
from app.admin_view import *

admin_app, rt = create_app_with_auth()

@admin_app.get("/backups")
def list_backups(auth):
    files = get_backup_files()
    return render_backups_list(files, auth)

@admin_app.get("/backups/{file}")
def download_backup(file: str):
    return FileResponse(f"data/backup/{file}", media_type="application/octet-stream")

@admin_app.get("/backup")
def backup_active_db():
    try:
        backup_path = create_backup_model()
        return FileResponse(backup_path, filename="quran_backup.db")
    except FileNotFoundError:
        return Titled("Error", P("Database file not found"))
    except Exception as e:
        return Titled("❌ Error", P(f"Error creating backup: {e}"))

@admin_app.get("/tables")
def list_tables(auth):
    return tables_main_area(auth=auth)

@admin_app.get("/tables/{table}")
def view_table(table: str, auth):
    records = get_table_records(table)
    columns = get_column_headers(table)
    return render_table_view(table, records, columns, auth)

@admin_app.get("/tables/{table}/{primary_key}/edit")
def edit_record_view(table: str, primary_key: str, auth):
    primary_key = parse_primary_key(table, primary_key)
    current_data = get_record(table, primary_key)
    if table == "plans":
        current_data.completed = str(current_data.completed)
    return render_edit_record_view(table, primary_key, current_data, auth)

@admin_app.put("/tables/{table}/{primary_key}")
async def update_record(table: str, primary_key: str, redirect_link: str, req: Request):
    primary_key = parse_primary_key(table, primary_key)
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    current_data = {
        key: (value if value != "" else None)
        for key, value in current_data.items()
        if key != "redirect_link"
    }
    update_record_model(table, primary_key, current_data)
    return RedirectResponse(redirect_link, status_code=303)

@admin_app.delete("/tables/{table}/{primary_key}")
def delete_record(table: str, primary_key: str):
    try:
        primary_key = parse_primary_key(table, primary_key)
        delete_record_model(table, primary_key)
    except Exception as e:
        return Tr(Td(P(f"Error: {e}"), colspan="11", cls="text-center"))

@admin_app.get("/tables/{table}/new")
def new_record_view(table: str, auth):
    return render_new_record_view(table, auth)

@admin_app.post("/tables/{table}")
async def create_new_record(table: str, req: Request):
    formt_data = await req.form()
    current_data = formt_data.__dict__.get("_dict")
    insert_record_model(table, current_data)
    return Redirect(f"/admin/tables/{table}")

@admin_app.get("/tables/{table}/export")
def export_specific_table(table: str):
    csv_buffer = export_table_csv(table)
    file_name = f"{table}.csv"
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )

@admin_app.get("/tables/{table}/import")
def import_specific_table_view(table: str, auth):
    return render_import_view(table, auth)

@admin_app.post("/tables/{table}/import/preview")
async def import_specific_table_preview(table: str, file: UploadFile):
    file_content = await file.read()
    columns, records = process_csv_preview(table, file_content)
    return render_import_preview(table, file.filename, columns, records)

@admin_app.post("/tables/{table}/import")
async def import_specific_table(table: str, file: UploadFile):
    create_backup_model()
    file_content = await file.read()
    process_csv_import(table, file_content)
    return Redirect(f"/admin/tables/{table}")