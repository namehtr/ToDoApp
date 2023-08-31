from bson.objectid import ObjectId
import bcrypt

# No mongo initialization here

def get_user_by_email(email, mongo):
    users = mongo.db.users
    return users.find_one({'username': email})

def add_user(email, password, mongo):
    users = mongo.db.users
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({
        "username": email,
        "password": hashed_pw
    })

def get_all_todos_by_email(email, mongo):
    return list(mongo.db.todo.find({"username": email, "completed": False}))

def add_todo_for_email(email, text, mongo):
    todo_data = {
        "text": text,
        "completed": False,
        "subtasks": [],
        "username": email
    }
    mongo.db.todo.insert_one(todo_data)

def get_todo_by_id(todo_id, mongo):
    return mongo.db.todo.find_one({"_id": ObjectId(todo_id)})

def add_subtask_to_todo(todo_id, subtask_name, mongo):
    subtask = {
        "_id": ObjectId(),
        "text": subtask_name,
        "completed": False
    }
    mongo.db.todo.update_one({"_id": ObjectId(todo_id)}, {"$push": {"subtasks": subtask}})

def update_todo_status(todo_id, status, mongo):
    mongo.db.todo.update_one({'_id': ObjectId(todo_id)}, {'$set': {'completed': status}})

def update_subtask_status(subtask_id, status, mongo):
    mongo.db.todo.update_one({'subtasks._id': ObjectId(subtask_id)}, {'$set': {'subtasks.$.completed': status}})