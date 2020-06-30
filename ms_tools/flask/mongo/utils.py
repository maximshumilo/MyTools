from mongoengine.errors import ValidationError as MongoValidationError


def save_doc(obj):
    """ Save doc in mongodb """
    try:
        obj.save()
    except MongoValidationError as exc:
        errors = {field: str(error) for field, error in exc.errors.items()}
        return {"errors": errors}
    return None
