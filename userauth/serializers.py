from rest_framework import serializers

from . models import *
from django.contrib.auth.models import User

from typing import Dict, Any


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','email']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['full_name','phone','nationality','preferred_destination']

class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    password1 = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    agreed_to_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = Profile
        fields = ['full_name', 'phone', 'email', 'username', 'password', 'password1', 
                  'agreed_to_terms', 'nationality', 'preferred_destination']

    def validate(self, data):
        # Check password match
        if data['password'] != data['password1']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        
        # Check agreed to terms
        if not data.get('agreed_to_terms'):
            raise serializers.ValidationError(
                {'agreed_to_terms': 'You must agree to the terms and conditions to register.'}
            )
        
        # Check if username exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({'username': 'Username already exists'})
        
        # Check if email exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Email already exists'})
        
        return data
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        validated_data.pop('password1')
        validated_data.pop('agreed_to_terms')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile = Profile.objects.create(
            user=user,
            full_name=validated_data['full_name'],
            phone=validated_data['phone'],
            nationality=validated_data['nationality'],
            preferred_destination=validated_data['preferred_destination'],
            agreed_to_terms=True,  # Set to True since validation passed
            is_verified=False
        )
        return profile