import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
app.app_context().push()
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    qDrinks = Drink.query.order_by(Drink.id).all()

    if len(qDrinks) == 0:
        abort(404)

    drinks = [drink.short() for drink in qDrinks]

    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )


'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    qDrinks = Drink.query.order_by(Drink.id).all()

    if len(qDrinks) == 0:
        abort(404)

    drinks = [drink.long() for drink in qDrinks]

    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    try:
        body = request.get_json()

        new_title = body.get("title", None)
        new_recipe = body.get("recipe", None)
        if new_title is None or new_recipe is None:
            abort(400)

        new_drink = Drink(
            title = new_title,
            recipe = json.dumps(new_recipe)
        )

        new_drink.insert()

        drink = [new_drink.long()]

        return jsonify(
            {
                "success": True,
                "drinks": drink
            }
        )
    except:
        abort(422)


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    try:
        qDrink = Drink.query.filter(Drink.id == id).one_or_none()

        if qDrink is None:
            abort(404)

        body = request.get_json()

        update_title = body.get("title", None)
        update_recipe = body.get("recipe", None)
        if update_title is None and update_recipe is None:
            abort(400)
        elif update_title is not None:
            qDrink.title = update_title
        elif update_recipe is not None:
            qDrink.recipe = json.dumps(update_recipe)

        qDrink.recipe = json.dumps(update_recipe)

        drink = [qDrink.long()]

        return jsonify(
            {
                "success": True,
                "drinks": drink
            }
        )
    except:
        abort(422)

'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('patch:drinks')
def remove_drink(jwt, id):
    try:
        qDrink = Drink.query.filter(Drink.id == id).one_or_none()

        if qDrink is None:
            abort(404)

        qDrink.delete()

        return jsonify(
            {
                "success": True,
                "delete": id
            }
        )
    except:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify(
        {
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }
    ), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify(
        {
            "success": False,
            "error": 400,
            "message": "bad request"
        }
    ), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify(
        {
            "success": False,
            "error": 404,
            "message": "not found"
        }
    ), 404

@app.errorhandler(500)
def server_internal_erro(error):
    return jsonify(
        {
            "success": False,
            "error": 500,
            "message": "server internal error"
        }
    ), 500

@app.errorhandler(AuthError)
def authorization_error(error):
    return jsonify(
        {
            "success": False,
            "error": error.status_code,
            "message": error.error
        }
    ), error.status_code