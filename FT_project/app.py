from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)


def get_script_from_git(url):
    """Функция для загрузки скрипта из Git по ссылке."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Не удалось загрузить скрипт из {url}. Ошибка: {e}")


def generate_sql_query(schema_src, object_src, schema, object, keys, attributes, git_script_url=None):
    attributes_str = ", ".join(attributes)
    keys_conditions = " and ".join([f"ist.{key}=pr.{key}" for key in keys])
    where_conditions = " or ".join([f"pr.{key} is null" for key in keys])
    where_conditions += " or " + " or ".join(
        [f"decode(ist.{attr}, pr.{attr}, 0, 1)=1" for attr in attributes if attr not in keys])

    git_script = ""
    if git_script_url:
        git_script = get_script_from_git(git_script_url)
        git_script = f"with algoritm as ({git_script}),\n"

    sql_query = f"""
    {git_script}ist as (
        select {attributes_str}
        from {object_src}.{schema_src}
    ),
    pr as (
        select {attributes_str}
        from {schema}.{object}
    )
    select {", ".join([f"ist.{attr}, pr.{attr}" for attr in attributes])}
    from ist
    left join pr on {keys_conditions}
    where {where_conditions};
    """

    return sql_query


@app.route("/")
def index():
    """Рендерим главную страницу."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """Обрабатываем запрос на генерацию SQL."""
    data = request.json
    schema_src = data.get("schema_src")
    object_src = data.get("object_src")
    schema = data.get("schema")
    object = data.get("object")
    keys = data.get("keys", [])  # Список ключей
    attributes = data.get("attributes", [])  # Список атрибутов
    git_script_url = data.get("git_script_url")

    try:
        sql_query = generate_sql_query(schema_src, object_src, schema, object, keys, attributes, git_script_url)
        return jsonify({"success": True, "sql_query": sql_query})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)