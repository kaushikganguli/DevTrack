from django.shortcuts import render

# Create your views here.
import json
import os
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Reporter,
    Issue,
    CriticalIssue,
    LowPriorityIssue
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTERS_FILE = os.path.join(BASE_DIR, "reporters.json")
ISSUES_FILE = os.path.join(BASE_DIR, "issues.json")


def read_json(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def write_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


@csrf_exempt
def reporters(request):

    # POST /api/reporters/
    if request.method == "POST":

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"},
                status=400
            )

        try:
            reporter = Reporter(
                id=data["id"],
                name=data["name"],
                email=data["email"],
                team=data["team"]
            )

            reporter.validate()

        except KeyError as e:
            return JsonResponse(
                {"error": f"Missing field: {e.args[0]}"},
                status=400
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400
            )

        reporters_data = read_json(REPORTERS_FILE)

        for existing in reporters_data:
            if existing["id"] == reporter.id:
                return JsonResponse(
                    {"error": "Reporter ID already exists"},
                    status=400
                )

        reporters_data.append(reporter.to_dict())
        write_json(REPORTERS_FILE, reporters_data)

        return JsonResponse(
            reporter.to_dict(),
            status=201
        )

    # GET /api/reporters/
    if request.method == "GET":

        reporters_data = read_json(REPORTERS_FILE)

        reporter_id = request.GET.get("id")

        if reporter_id:
            try:
                reporter_id = int(reporter_id)
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid reporter ID"},
                    status=400
                )

            for reporter in reporters_data:
                if reporter["id"] == reporter_id:
                    return JsonResponse(
                        reporter,
                        status=200
                    )

            return JsonResponse(
                {"error": "Reporter not found"},
                status=404
            )

        return JsonResponse(
            reporters_data,
            safe=False,
            status=200
        )

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )


@csrf_exempt
def issues(request):

    # POST /api/issues/
    if request.method == "POST":

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"},
                status=400
            )

        required_fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "reporter_id"
        ]

        for field in required_fields:
            if field not in data:
                return JsonResponse(
                    {"error": f"Missing field: {field}"},
                    status=400
                )

        reporters_data = read_json(REPORTERS_FILE)

        reporter_exists = any(
            reporter["id"] == data["reporter_id"]
            for reporter in reporters_data
        )

        if not reporter_exists:
            return JsonResponse(
                {"error": "Reporter not found"},
                status=404
            )

        # Choose subclass based on priority
        if data["priority"] == "critical":
            issue = CriticalIssue(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=data["priority"],
                reporter_id=data["reporter_id"],
                created_at=str(datetime.now())
            )

        elif data["priority"] == "low":
            issue = LowPriorityIssue(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=data["priority"],
                reporter_id=data["reporter_id"],
                created_at=str(datetime.now())
            )

        else:
            issue = Issue(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=data["priority"],
                reporter_id=data["reporter_id"],
                created_at=str(datetime.now())
            )

        try:
            issue.validate()

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400
            )

        issues_data = read_json(ISSUES_FILE)

        for existing in issues_data:
            if existing["id"] == issue.id:
                return JsonResponse(
                    {"error": "Issue ID already exists"},
                    status=400
                )

        issue_data = issue.to_dict()

        # The assignment requires the message in the POST response.
        issue_data["message"] = issue.describe()

        # Store the actual issue without the response message.
        stored_issue = issue.to_dict()

        issues_data.append(stored_issue)
        write_json(ISSUES_FILE, issues_data)

        return JsonResponse(
            issue_data,
            status=201
        )

    # GET /api/issues/
    if request.method == "GET":

        issues_data = read_json(ISSUES_FILE)

        issue_id = request.GET.get("id")
        status_filter = request.GET.get("status")

        # GET /api/issues/?id=1
        if issue_id:

            try:
                issue_id = int(issue_id)
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid issue ID"},
                    status=400
                )

            for issue in issues_data:

                if issue["id"] == issue_id:
                    return JsonResponse(
                        issue,
                        status=200
                    )

            return JsonResponse(
                {"error": "Issue not found"},
                status=404
            )

        # GET /api/issues/?status=open
        if status_filter:

            filtered_issues = [
                issue
                for issue in issues_data
                if issue["status"] == status_filter
            ]

            return JsonResponse(
                filtered_issues,
                safe=False,
                status=200
            )

        # GET /api/issues/
        return JsonResponse(
            issues_data,
            safe=False,
            status=200
        )

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )