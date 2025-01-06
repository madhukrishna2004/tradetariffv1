import logging
import math
import os
from concurrent.futures.thread import ThreadPoolExecutor

from elasticapm.contrib.flask import ElasticAPM
import flask
from flask import request, Response, jsonify, render_template
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from whitenoise import WhiteNoise
import openai
from dotenv import load_dotenv
from cryptography.fernet import Fernet

from src import decorators, utils

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

if os.getenv("SENTRY_KEY") and os.getenv("SENTRY_PROJECT") and os.getenv("SENTRY_HOST"):
    sentry_sdk.init(
        dsn=f"https://{os.getenv('SENTRY_KEY')}@{os.getenv('SENTRY_HOST')}/{os.getenv('SENTRY_PROJECT')}",
        integrations=[FlaskIntegration()],
    )

app = flask.Flask(__name__)

# Enable template auto-reload to refresh templates during development
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Disable caching for static files during development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching

# Elastic APM configuration
app.config["ELASTIC_APM"] = {
    "SERVICE_NAME": "global-uk-tariff",
    "SECRET_TOKEN": os.getenv("APM_TOKEN"),
    "SERVER_URL": "https://apm.elk.uktrade.digital",
    "ENVIRONMENT": os.getenv("ENV_NAME"),
}

# Disable caching for static files by setting autorefresh to True
app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/", autorefresh=True)
apm = ElasticAPM(app)

# Generate a key for encryption (make sure to store this key securely for later decryption)
def generate_encryption_key():
    return Fernet.generate_key()

# Save the encryption key securely (You should store this somewhere safe and private)
def save_encryption_key(key):
    with open("encryption_key.key", "wb") as key_file:
        key_file.write(key)

# Load the encryption key (use this when you need to decrypt)
def load_encryption_key():
    with open("encryption_key.key", "rb") as key_file:
        return key_file.read()

# Encrypt the parts of the API key
def encrypt_api_key_parts(part1, part2, encryption_key):
    cipher = Fernet(encryption_key)
    encrypted_part1 = cipher.encrypt(part1.encode())
    encrypted_part2 = cipher.encrypt(part2.encode())
    
    # Save the encrypted parts to a file
    with open("encrypted_api_key_parts.txt", "wb") as encrypted_file:
        encrypted_file.write(encrypted_part1 + b'\n' + encrypted_part2)

# Decrypt the API key parts and combine them
def decrypt_api_key_parts(encrypted_file_path, encryption_key):
    cipher = Fernet(encryption_key)
    
    # Read the encrypted parts from the file
    with open(encrypted_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read().split(b'\n')
        encrypted_part1 = encrypted_data[0]
        encrypted_part2 = encrypted_data[1]
    
    # Decrypt the parts
    decrypted_part1 = cipher.decrypt(encrypted_part1).decode()
    decrypted_part2 = cipher.decrypt(encrypted_part2).decode()
    
    # Combine the decrypted parts to form the API key
    return decrypted_part1 + decrypted_part2

#Encrypt and save API key parts if not already done (run this separately first)
#Example for encrypting and saving the API key parts:
part1 = "sk-proj-Jcgx4YzLqRFQq9F9MXwTfq2sk_q1HwfklOFIviaF45ockbK_K7HIUDUngcXZH6ka3jI0kxXYU1T3"
part2 = "BlbkFJjKGwgEWutYmHyXYAzNCozAUvZVgvDT8wzlhe2sNmugk628iD4XHcmflri96tUZbi-E4J24l14A"
encryption_key = generate_encryption_key()
save_encryption_key(encryption_key)
encrypt_api_key_parts(part1, part2, encryption_key)

# Load the encryption key
encryption_key = load_encryption_key()

# Decrypt and combine the API key parts
openai.api_key = decrypt_api_key_parts("encrypted_api_key_parts.txt", encryption_key)

thread_pool = ThreadPoolExecutor()

# Generate cache-busting version string
VERSION = f"?v={int(os.path.getmtime(__file__))}"  # Based on the file modification time


@app.route("/")
def home():
    return flask.redirect("/tariff")


@app.route("/accessibility", strict_slashes=False)
def accessibility():
    return flask.render_template("accessibility.html", version=VERSION)


@app.route("/tariff")
@decorators.cache_without_request_args(
    q=utils.DEFAULT_FILTER, p=utils.DEFAULT_PAGE, n=utils.DEFAULT_SAMPLE_SIZE
)
@decorators.compress_response
def tariff():
    data, total = utils.get_data_from_request()
    page = utils.get_positive_int_request_arg("p", utils.DEFAULT_PAGE)
    sample_size = utils.get_positive_int_request_arg("n", utils.DEFAULT_SAMPLE_SIZE)
    max_page = math.ceil(total / sample_size)

    return flask.render_template(
        "tariff.html",
        all_data=utils.get_data(get_all=True)[0],
        data=data,
        total=total,
        pages=utils.get_pages(page, max_page),
        page=page,
        max_page=total / sample_size,
        sample_size=sample_size,
        start_index=(sample_size * (page - 1)) + 1 if len(data) != 0 else 0,
        stop_index=sample_size * page if sample_size * page < total else total,
        version=VERSION,
    )


@app.route("/api/global-uk-tariff.csv")
@decorators.cache_without_request_args(
    q=utils.DEFAULT_FILTER, p=utils.DEFAULT_PAGE, n=utils.DEFAULT_SAMPLE_SIZE
)
@decorators.compress_response
def tariff_csv():
    filter_arg = request.args.get(utils.FILTER_ARG)
    data = utils.get_data_as_list(filter_arg)
    output = utils.format_data_as_csv(data)
    return flask.send_file(output, mimetype="text/csv")


@app.route("/api/global-uk-tariff.xlsx")
@decorators.cache_without_request_args(
    q=utils.DEFAULT_FILTER, p=utils.DEFAULT_PAGE, n=utils.DEFAULT_SAMPLE_SIZE
)
@decorators.compress_response
def tariff_xlsx():
    filter_arg = request.args.get(utils.FILTER_ARG)
    data = utils.get_data_as_list(filter_arg)
    output = utils.format_data_as_xlsx(data)
    return flask.send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/api/global-uk-tariff")
@decorators.cache_without_request_args(
    q=utils.DEFAULT_FILTER, p=utils.DEFAULT_PAGE, n=utils.DEFAULT_SAMPLE_SIZE
)
@decorators.compress_response
def tariff_api():
    data = utils.get_data_from_request(get_all=True)[0]
    return flask.jsonify(data)


@app.route("/tariff/metadata.json")
@decorators.cache_without_request_args()
@decorators.compress_response
def tariff_metadata():
    return flask.Response(
        flask.render_template("metadata.json"), mimetype="application/json",
    )


@app.route("/tariff/metadata.xml")
@decorators.cache_without_request_args()
@decorators.compress_response
def dcat_metadata():
    return flask.Response(
        flask.render_template("metadata.xml"), mimetype="application/rdf+xml",
    )


@app.route("/chatbot.html")
def chatbot():
    return flask.render_template("chatbot.html", version=VERSION)


@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Get the user message from the request
        user_message = request.json.get("message", "")
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # OpenAI API call for the chatbot response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=200,
            temperature=0.6,
        )
        
        # Get the response from OpenAI
        bot_reply = response['choices'][0]['message']['content']
        
        return jsonify({"response": bot_reply})
    except Exception as e:
        logger.error(f"Error occurred while processing the chatbot message: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.after_request
def set_cache_control_headers(response: Response):
    # Add headers to disable caching for all responses
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # Prevent search engines from indexing the site
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.after_request
def google_analytics(response: Response):
    try:
        kwargs = {}
        if request.accept_languages:
            try:
                kwargs["ul"] = request.accept_languages[0][0]
            except IndexError:
                pass

        if request.referrer:
            kwargs["dr"] = request.referrer

        path = request.path
        if request.query_string:
            path = path + f"?{request.query_string.decode()}"

        thread_pool.submit(
            utils.send_analytics,
            path=path,
            host=request.host,
            remote_addr=request.remote_addr,
            user_agent=request.headers["User-Agent"],
            **kwargs,
        )
    except Exception:  # We don't want to kill the response if GA fails.
        logger.exception("Google Analytics failed")
        pass
    return response


if __name__ == "__main__":
    app.run(debug=True)
