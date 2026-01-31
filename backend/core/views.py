from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.core.exceptions import ValidationError
from .ingestion_utils import (
    parse_classroom_csv, 
    parse_faculty_csv,
    parse_course_csv,
    parse_section_csv,
    parse_assignment_csv
)

class UploadCSVView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, type=None):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.FILES['file']
        
        try:
            if type == 'classrooms':
                result = parse_classroom_csv(file_obj)
            elif type == 'faculty':
                result = parse_faculty_csv(file_obj)
            elif type == 'courses':
                result = parse_course_csv(file_obj)
            elif type == 'sections':
                result = parse_section_csv(file_obj)
            elif type == 'assignments':
                result = parse_assignment_csv(file_obj)
            else:
                return Response({"error": "Invalid upload type."}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "message": "Upload successful",
                "details": result
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
