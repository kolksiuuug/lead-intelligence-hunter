from flask import jsonify

def error_handler(app):
    @app.errorhandler(404)
    def not_found(error):return jsonify({"error":"not found", "message":"resource not found"}, 404)

    @app.errorhandler(500)
    def internal_error(error):return jsonify({"error":"internal server error", "message":"the server does not respond on this request"}, 500)

    @app.errorhandler(400)
    def bad_request(error):return jsonify({"error":"bad request", "message":"request was wrong"}, 400) 

    @app.errorhandler(429)
    def too_many_requests(error):return jsonify({"error":"too many requests", "message":"your messages are too fast"}, 429)

    @app.errorhandler(502)
    def timeout(error):return jsonify({"error":"backend timeout"})