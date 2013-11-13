from flask import Flask, render_template
from ircsay import WordStatTool

app = Flask("IRCSay")


wst = WordStatTool("output.json")

@app.route("/")
def index():
    sentence = wst.generate_sentence()
    return render_template("index.html", sentence=sentence)
    


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=1234)

