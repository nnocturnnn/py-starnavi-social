import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone
from django.utils.timezone import now
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Like, Post
from .serializers import AnalyticsSerializer, PostSerializer, UserSerializer

logger = logging.getLogger('api')
User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=UserSerializer,
        responses={201: UserSerializer()}
    )
    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User created successfully: {user.username}")
            return Response({
                'status': 'User created successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        logger.error(f"Signup failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Login user and return JWT tokens",
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={"application/json": {"status": "Login successful",
                                               "refresh": "jwt_refresh_token",
                                               "access": "jwt_access_token",
                                               "user": {"username": "testuser",
                                                         "email": "testuser@example.com"}}}  # noqa E501
            ),
            401: openapi.Response(description="Invalid credentials")
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = User.objects.filter(username=username).first()
        if user and user.verify_password(password):
            refresh = RefreshToken.for_user(user)
            logger.info(f"Login successful for user: {username}")
            return Response({
                'status': 'Login successful',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        logger.warning(f"Authentication failed for user: {username}")
        return Response({'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_description="Get user activity details",
        responses={
            200: openapi.Response(
                description="User activity details",
                examples={"application/json": {"status": "User activity retrieved successfully",  # noqa E501
                                               "last_login": "2023-05-26T00:00:00Z",
                                               "last_request": "2023-05-26T00:00:00Z"}}
            )
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def activity(self, request):
        user = request.user
        return Response({
            'status': 'User activity retrieved successfully',
            'last_login': user.last_login,
            'last_request': user.last_request,
        })

    def perform_authentication(self, request):
        user = request.user
        if not user.is_authenticated:
            return
        user.last_request = now()
        user.save()


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        logger.info(f"Post created successfully by user: {self.request.user.username}")
        return Response({
            'status': 'Post created successfully',
            'post': PostSerializer(post).data
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Like a post",
        responses={
            200: openapi.Response(description="Post liked successfully"),
            400: openapi.Response(description="Post already liked")
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        return self._like_unlike_post(request, pk, like=True)

    @swagger_auto_schema(
        operation_description="Unlike a post",
        responses={
            200: openapi.Response(description="Post unliked successfully"),
            400: openapi.Response(description="Post not liked yet")
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        return self._like_unlike_post(request, pk, like=False)

    def _like_unlike_post(self, request, pk, like=True):
        post = self.get_object()
        user = request.user
        like_instance, created = Like.objects.get_or_create(user=user, post=post)
        if like:
            if created:
                logger.info(f"Post liked successfully: {
                            post.id} by user: {user.username}")
                return Response({
                    'status': 'Post liked successfully',
                    'post': PostSerializer(post).data,
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            logger.warning(f"Post already liked: {post.id} by user: {user.username}")
            return Response({
                'status': 'Post already liked',
                'post': PostSerializer(post).data,
                'user': UserSerializer(user).data
            }, status=status.HTTP_400_BAD_REQUEST)
        if not created:
            like_instance.delete()
            logger.info(f"Post unliked successfully: {post.id} by user: {user.username}")
            return Response({
                'status': 'Post unliked successfully',
                'post': PostSerializer(post).data,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        logger.warning(f"Post not liked yet: {post.id} by user: {user.username}")
        return Response({
            'status': 'Post not liked yet',
            'post': PostSerializer(post).data,
            'user': UserSerializer(user).data
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Retrieve analytics data for likes between two dates",
        manual_parameters=[
            openapi.Parameter('date_from', openapi.IN_QUERY,
                              description="Start date in YYYY-MM-DD format",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY,
                              description="End date in YYYY-MM-DD format",
                              type=openapi.TYPE_STRING),
        ],
        responses={200: AnalyticsSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def analytics(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        cache_key = f'analytics_{date_from}_{date_to}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("Analytics data retrieved from cache")
            return Response({
                'status': 'Analytics data retrieved successfully (from cache)',
                'data': cached_data
            })

        if not date_from or not date_to:
            logger.error("Analytics request missing date_from or date_to parameters")
            return Response({"error": "date_from and date_to are required parameters"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()

            likes_data = Like.objects.filter(date__date__range=[date_from, date_to])\
                .values('date__date')\
                .annotate(count=Count('public_id'))
            serializer = AnalyticsSerializer(likes_data, many=True)
            logger.info("Analytics data retrieved successfully")
            cache.set(cache_key, serializer.data, timeout=60*60)
            return Response({
                'status': 'Analytics data retrieved successfully',
                'data': serializer.data
            })
        except ValueError as e:
            logger.error(f"Error parsing dates: {e}")
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST)
