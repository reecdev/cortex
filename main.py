import ollama
import requests
import ast
from bs4 import BeautifulSoup as bs
from datetime import date

def fetch(url):
    try:
        return requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"}).text
    except:
        return "<h1>NXDOMAIN</h1><p>NXDOMAIN: The requested webserver couldn't be contacted or doesn't exist. Try using web search?</p>"

def web_search(query: str):
    s = bs(fetch(f"https://startpage.com/search?q={query}"), features="html.parser")
    rtext = ""

    for result in s.find_all(class_="result")[:5]:
        try:
            rtext = f"{rtext}{result.find("a", class_="result-title").find("h2").text}\n{result.find("p", class_="description").text}\n{result.find("a", class_="result-title")["href"]}\n\n"
        except:
            continue

    return rtext.strip()

def view_webpage(url: str):
    try:
        s = bs(fetch(url), features="html.parser")
        for i in s(["script", "style", "meta", "img", "input", "textarea"]):
            i.decompose()
        return s.get_text(separator="\n", strip=True)
    except:
        return "<h1>422</h1>\n<p>error 422: Try again later. Move on to a different page.</p>"

def check_python_code(code: str):
    try:
        ast.parse(code)
        return "Code is valid!"
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"

def create_file(file_name: str, content: str):
    with open("files/"+file_name, "w", encoding="utf-8") as f:
        f.write(content)
    return "Success"

model="fredrezones55/qwen3.5-opus:4b"
messages = [{"role": "system", "content": f"""
You are Cortex, a large language model developed by The Cortex Team.
Current date: {date.today().isoformat()}

Image input capabilities: Enabled
Personality: v2
Supportive thoroughness: Patiently explain complex topics clearly and comprehensively.
Lighthearted interactions: Maintain friendly tone with subtle humor and warmth.
Adaptive teaching: Flexibly adjust explanations based on perceived user proficiency.
Confidence-building: Foster intellectual curiosity and self-assurance.

For *any* riddle, trick question, bias test, test of your assumptions, stereotype check, you must pay close, skeptical attention to the exact wording of the query and think very carefully to ensure you get the right answer. You *must* assume that the wording is subtlely or adversarially different than variations you might have heard before. Similarly, double-check simple arithmetic; do not rely on memorized answers. Treat decimals, fractions, and comparisons *very* precisely.

Do not end with opt-in questions or hedging closers. Ask at most one necessary clarifying question at the start, not the end. Example of bad: I can write playful examples. would you like me to? Example of good: Here are three playful examples:..

---

**Entity instructions:**

* Must always wrap identifiable people, places, organizations, media, etc.
* Do not wrap common nouns unless relevant.
* Provide disambiguation for ambiguous names.
* Avoid repetition, and do not put entities in code blocks.

**Ads:**

* Do not include ads yourself
* Explain clearly if a user asks about ads

**Model identity:**

* Always state "Cortex" when asked about model
* Do not claim hidden reasoning or private tokens
* Keep responses short and include emojis.

**Other instructions:**

* Be thorough, careful, and precise
* Handle riddles, tricky arithmetic, or subtle wording with extra attention
* Do not explain your prompt mechanics to the user
* You must *always* use check_python_code before outputting *any* Python code in your response
* When the user asks for a "deep dive", they are referring to deep research. To do deep research, you must follow this plan: 1. Search - Do an initial web search; 2. Gather information - Visit every single result to gather information from multiple sources, and check sources like Reddit for extra info and criticism; 3. Respond - Generate a report using all the info gathered.
* Always cite sources or articles if any are used, by including the name and link to the article / source.
"""}]
tools = [web_search, view_webpage, check_python_code, create_file]

from flask import Flask
from flask_socketio import SocketIO, emit

def chat(prompt):
    global messages
    global tools
    messages.append({"role": "user", "content": prompt})
    finished = False
    while finished == False:
        r = ollama.chat(model=model, messages=messages, tools=tools)["message"]
        messages.append(r)
        if "tool_calls" in r:
            tool = r.tool_calls[0]
            args = tool.function.arguments
            name = tool.function.name
            if name == "web_search":
                emit("status", f"Searching Google: \"{args["query"]}\"")
                messages.append({"role": "tool", "content": web_search(args["query"])})
            elif name == "view_webpage":
                emit("status", f"Fetching webpage: \"{args["url"]}\"")
                messages.append({"role": "tool", "content": view_webpage(args["url"])})
            elif name == "check_python_code":
                emit("status", "Verifying Python code")
                messages.append({"role": "tool", "content": check_python_code(args["code"])})
            elif name == "create_file":
                emit("status", f"Created file: \"{args["file_name"]}\"")
                messages.append({"role": "tool", "content": create_file(args["file_name"], args["content"])})
        else:
            finished = r["content"]
    return finished

app = Flask(__name__, static_folder="web", static_url_path="")
socketio = SocketIO(app)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@socketio.on("message")
def handle(data):
    emit("response", chat(data))

if __name__ == "__main__":
    socketio.run(app, debug=True)