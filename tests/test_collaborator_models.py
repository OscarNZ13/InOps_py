from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.modules.collaborators.models import Collaborator, CollaboratorProfile


def add_collaborator(initials, signature, email=None, **names):
    names = {"first_name": "Oscar", "last_name": "Naranjo", **names}
    collaborator = Collaborator(birthdate=date(1995, 5, 20), **names)
    collaborator.profile = CollaboratorProfile(initials=initials, signature=signature, email=email)
    db.session.add(collaborator)
    db.session.commit()
    return collaborator


def assert_rejected(*args, **kwargs):
    with pytest.raises(IntegrityError):
        add_collaborator(*args, **kwargs)
    db.session.rollback()


def test_collaborator_and_profile_are_linked(app):
    collaborator = add_collaborator("ONA", "ONaranjo", email="oscar@empresa.com")
    db.session.expire_all()

    saved = db.session.get(Collaborator, collaborator.id_collab)
    assert saved.profile.initials == "ONA"
    assert saved.profile.signature == "ONaranjo"
    assert saved.profile.collaborator is saved
    assert saved.is_active
    assert saved.created_at is not None and saved.profile.created_at is not None


@pytest.mark.parametrize(
    "names, expected",
    [
        ({}, "Oscar Naranjo"),
        ({"second_name": "Josue", "second_last_name": "Zuniga"}, "Oscar Josue Naranjo Zuniga"),
        ({"second_last_name": "Zuniga"}, "Oscar Naranjo Zuniga"),
    ],
)
def test_full_name_skips_missing_parts(names, expected):
    assert Collaborator(first_name="Oscar", last_name="Naranjo", **names).full_name == expected


def test_initials_must_be_unique(app):
    add_collaborator("ONZ", "ONaranjo")
    assert_rejected("ONZ", "ONaranjoZ")


def test_signature_must_be_unique(app):
    add_collaborator("ONZ", "ONaranjo")
    assert_rejected("ONZ1", "ONaranjo")


def test_email_is_unique_only_when_present(app):
    add_collaborator("ONZ", "ONaranjo")
    add_collaborator("ONZ1", "ONaranjoZ")
    add_collaborator("ONZ2", "ONaranjoZ1", email="oscar@empresa.com")
    assert_rejected("ONZ3", "ONaranjoZ2", email="oscar@empresa.com")
    assert db.session.query(CollaboratorProfile).count() == 3


def test_only_one_profile_per_collaborator(app):
    collaborator = add_collaborator("ONZ", "ONaranjo")
    db.session.add(CollaboratorProfile(id_collab=collaborator.id_collab, initials="ONZ1", signature="ONaranjoZ"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_profile_requires_existing_collaborator(app):
    db.session.add(CollaboratorProfile(id_collab=999, initials="ONZ", signature="ONaranjo"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
