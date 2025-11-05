from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken


from django.conf.global_settings import SECRET_KEY
from django.contrib.auth import login,logout,authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
import  jwt
from django.conf import settings

from . models import *
from . serializers import *
from .serializers import RegistrationSerializer
from .utils import sendMail
from rest_framework.permissions import IsAuthenticated



class RegistrationView(APIView):
    def post(self, request):
        try:
            print("📥 Received data:", request.data)  # Debug log
            
            serializer = RegistrationSerializer(data=request.data)
            if serializer.is_valid():
                profile = serializer.save()
                user = profile.user

                # Generate token for email verification
                token = RefreshToken.for_user(user).access_token

                # Build activation URL
                current_site = get_current_site(request).domain
                relative_link = reverse('verify')
                abs_url = f"http://{current_site}{relative_link}?token={str(token)}"

                # Create HTML email content
                email_html = f"""
                <html>
                    <body>
                        <h2>Welcome {user.username}!</h2>
                        <p>Thank you for registering. Please verify your email by clicking the link below:</p>
                        <a href="{abs_url}" style="color: blue;">Verify your email</a>
                    </body>
                </html>
                """

                # Send activation email
                try:
                    sendMail(
                        subject="Verify your email",
                        html_content=email_html,
                        sender_email=settings.BREVO_SENDER_EMAIL,
                        recipient_email=user.email
                    )
                except Exception as email_error:
                    print(f"⚠️ Email sending failed: {email_error}")

                return Response(
                    {
                        "message": "Registration successful. Please check your email to verify your account.",
                        "user": {
                            "username": user.username,
                            "email": user.email,
                            "full_name": profile.full_name
                        }
                    },
                    status=status.HTTP_201_CREATED
                )

            print("❌ Validation errors:", serializer.errors)  # Debug log
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"❌ Exception: {str(e)}")  # Debug log
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class VerifyRegistrationView(generics.GenericAPIView):
    def get(self,request):
        token = request.GET.get('token')
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']

            user = get_object_or_404(User,id=user_id)

            profile = get_object_or_404(Profile,user=user)

            if not profile.is_verified:
                profile.is_verified = True
                profile.save()
            return Response({"Message":"Email Verification successful"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'Error':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    def post(self, request):
        try:
            # Accept only email for login
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email:
                return Response(
                    {'message': 'Email is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not password:
                return Response(
                    {'message': 'Password is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {'message': 'Invalid email or password'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Authenticate the user using their username (from the User model)
            authenticated_user = authenticate(username=user.username, password=password)
            
            if authenticated_user is not None:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(authenticated_user)
                
                # Get user profile data
                profile = Profile.objects.filter(user=authenticated_user).first()
                
                return Response({
                    'message': 'Login successful',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': authenticated_user.id,
                        'username': authenticated_user.username,
                        'email': authenticated_user.email,
                        'full_name': profile.full_name if profile else authenticated_user.username,
                        'is_verified': profile.is_verified if profile else False,
                    }
                }, status=status.HTTP_200_OK)
            
            return Response(
                {'message': 'Invalid email or password'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )     
        
class LogoutView(APIView):
    def post(self,request):
        try:
            logout(request)
            return Response({'message':"Logout was successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = get_object_or_404(Profile,user = request.user)
            application = getattr(profile, 'application', None)
            

            data = {
                "username": profile.full_name,
                "application_status": getattr(application, 'status', "No application found"),
                "social_links": {
                    "twitter": "https://twitter.com/feelnigeria",
                    "instagram": "https://instagram.com/feelnigeria",
                    "facebook": "https://facebook.com/feelnigeria",
                },
                "faqs": [
                    "How long does review take?",
                    "What documents are required?",
                    "Can I edit my application after submission?",
                ]
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)