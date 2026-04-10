# OAuth2 Multi-Gateway Authentication System

## Overview

This document describes the OAuth2 authentication mechanism for the Gymbo AI platform, which supports 4 different user types (admin, trainer, client, organisation) with separate gateways and isolated functionality. The system automatically selects the appropriate gateway for data fetching based on the user's role, ensuring each user type gets data from their own gateway for all routes they can access.

## Architecture

### User Types and Gateways

1. **Admin Gateway** (Port 8080)
   - Full system access
   - User management
   - System configuration
   - **Access**: All routes
   - **Data Source**: Admin gateway for all routes

2. **Trainer Gateway** (Port 8081)
   - Client management
   - Exercise supervision
   - Training data access
   - **Access**: `/app/exercise`, `/app/assessment`, `/app/client`, `/app/mobile`, `/app/desktop`
   - **Data Source**: Trainer gateway for all routes

3. **Client Gateway** (Port 8082)
   - Personal training data
   - Exercise tracking
   - Progress monitoring
   - **Access**: `/app/dashboard`, `/app/exercise`, `/app/assessment`, `/app/mobile`, `/app/desktop`
   - **Data Source**: Client gateway for all routes

4. **Organisation Gateway** (Port 8083)
   - Organisation management
   - Billing and settings
   - User provisioning
   - **Access**: `/app/exercise`, `/app/assessment`, `/app/client`
   - **Data Source**: Organisation gateway for all routes

## Dynamic Gateway Selection

### Route Access Control

Each user role can access specific routes:

```typescript
const roleRouteAccess: Record<UserRole, string[]> = {
  client: ['/app/dashboard', '/app/exercise', '/app/assessment', '/app/mobile', '/app/desktop'],
  trainer: ['/app/exercise', '/app/assessment', '/app/client', '/app/mobile', '/app/desktop'],
  organisation: ['/app/exercise', '/app/assessment', '/app/client'],
  admin: ['*'], // Admin can access all routes
};
```

### Data Gateway by User Role

The system determines which gateway to use for data fetching based on the user's role:

```typescript
const userRoleDataGateway: Record<UserRole, UserRole> = {
  client: 'client',        // Client gets data from client gateway
  trainer: 'trainer',      // Trainer gets data from trainer gateway
  organisation: 'organisation', // Organisation gets data from organisation gateway
  admin: 'admin',          // Admin gets data from admin gateway
};
```

**Key Principle**: Each user type gets data from their own gateway for all routes they can access.

## OAuth2 Flow

### 1. Route-Based Access Control

The frontend automatically checks if the current user can access the requested route:

```typescript
// Check if user can access this route
if (!canUserAccessRoute(user.role, pathname)) {
  // User doesn't have permission for this route
  router.push('/login?error=unauthorized');
  return;
}
```

### 2. Authentication Flow

1. **User visits protected route**
2. **Middleware checks authentication and permissions**
   - If no token → redirect to `/login?gateway=X&redirect=Y`
   - If user can't access route → redirect to `/login?error=unauthorized`
   - If wrong gateway → redirect to appropriate login
   - If valid token and permissions → allow access

3. **Login page shows gateway selection**
   - User selects their role
   - System generates OAuth2 authorization URL
   - User redirected to gateway's OAuth2 endpoint

4. **OAuth2 Authorization**
   - Gateway validates user credentials
   - Returns authorization code to callback URL

5. **Token Exchange**
   - Frontend exchanges code for access token
   - Stores token and user profile
   - Redirects to intended page

### 3. User Role-Based Data Gateway Selection

When a component needs to fetch data, the system automatically uses the gateway corresponding to the user's role:

```typescript
const { get } = useGatewayApi();

// Automatically uses the gateway based on user role
const exercises = await get('/api/exercises');
// - If user is client → calls client gateway
// - If user is trainer → calls trainer gateway
// - If user is admin → calls admin gateway
```

## Frontend Implementation

### Key Components

1. **AuthProvider** (`app/src/context/AuthProvider.tsx`)
   - Manages authentication state
   - Handles token refresh
   - Route-based access control
   - User role-based gateway selection

2. **AuthService** (`app/src/services/auth.ts`)
   - OAuth2 URL generation
   - Token exchange and refresh
   - User profile fetching
   - Gateway-specific API calls

3. **useGatewayApi** (`app/src/hooks/useGatewayApi.ts`)
   - Automatic gateway selection based on user role
   - HTTP method helpers (get, post, put, delete, patch)
   - Gateway override capability

4. **Middleware** (`app/src/middleware.ts`)
   - Route protection
   - Permission validation
   - Automatic redirects

### Configuration

Environment variables for each gateway:

```env
# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Admin Gateway OAuth2 Configuration
NEXT_PUBLIC_ADMIN_GATEWAY_URL=http://localhost:8080
NEXT_PUBLIC_ADMIN_CLIENT_ID=admin-client
ADMIN_CLIENT_SECRET=admin-secret

# Trainer Gateway OAuth2 Configuration
NEXT_PUBLIC_TRAINER_GATEWAY_URL=http://localhost:8081
NEXT_PUBLIC_TRAINER_CLIENT_ID=trainer-client
TRAINER_CLIENT_SECRET=trainer-secret

# Client Gateway OAuth2 Configuration
NEXT_PUBLIC_CLIENT_GATEWAY_URL=http://localhost:8082
NEXT_PUBLIC_CLIENT_CLIENT_ID=client-client
CLIENT_CLIENT_SECRET=client-secret

# Organisation Gateway OAuth2 Configuration
NEXT_PUBLIC_ORGANISATION_GATEWAY_URL=http://localhost:8083
NEXT_PUBLIC_ORGANISATION_CLIENT_ID=organisation-client
ORGANISATION_CLIENT_SECRET=organisation-secret
```

## Backend Implementation

### Gateway OAuth2 Endpoints

Each gateway provides these OAuth2 endpoints:

1. **Authorization Endpoint** (`/oauth/authorize`)
   - Accepts: `client_id`, `redirect_uri`, `scope`, `state`
   - Returns: Authorization code

2. **Token Endpoint** (`/oauth/token`)
   - Accepts: `grant_type`, `client_id`, `client_secret`, `code`/`refresh_token`
   - Returns: Access token, refresh token, user info

3. **User Profile Endpoint** (`/user/profile`)
   - Accepts: Bearer token
   - Returns: User profile with permissions

### Example Gateway Implementation

```go
type OAuth2Handler struct {
    config *oauth2.Config
    db     *database.GatewayDatabase
}

func (h *OAuth2Handler) Token(w http.ResponseWriter, r *http.Request) {
    // Validate client credentials
    // Exchange code for token
    // Return token response
}

func (h *OAuth2Handler) UserProfile(w http.ResponseWriter, r *http.Request) {
    // Validate Bearer token
    // Return user profile with permissions
}
```

## Usage Examples

### 1. Component Data Fetching

```typescript
import { useGatewayApi } from '@/hooks/useGatewayApi';

function ExerciseList() {
  const { get, post } = useGatewayApi();
  const [exercises, setExercises] = useState([]);

  useEffect(() => {
    // Automatically uses gateway based on user role
    const fetchExercises = async () => {
      const response = await get('/api/exercises');
      const data = await response.json();
      setExercises(data);
    };
    
    fetchExercises();
  }, []);

  const createExercise = async (exerciseData) => {
    // Automatically uses gateway based on user role
    await post('/api/exercises', exerciseData);
  };

  return (
    <div>
      {exercises.map(exercise => (
        <div key={exercise.id}>{exercise.name}</div>
      ))}
    </div>
  );
}
```

### 2. Gateway Override

```typescript
const { get } = useGatewayApi();

// Override automatic gateway selection
const response = await get('/api/clients', { 
  gateway: 'trainer' 
});
```

### 3. User Login Flow Examples

```typescript
// Client user visits /app/dashboard
// System checks: canUserAccessRoute('client', '/app/dashboard') → true
// System determines: getDataGatewayForUser('client') → 'client'
// Data comes from client gateway

// Trainer user visits /app/exercise
// System checks: canUserAccessRoute('trainer', '/app/exercise') → true
// System determines: getDataGatewayForUser('trainer') → 'trainer'
// Data comes from trainer gateway

// Admin user visits any route
// System checks: canUserAccessRoute('admin', '/app/exercise') → true
// System determines: getDataGatewayForUser('admin') → 'admin'
// Data comes from admin gateway
```

### 4. Navigation Based on Permissions

```typescript
// Navigation links are filtered based on user role
const filteredLinks = allLinks.filter(link => 
  canUserAccessRoute(user.role, link.href)
);
```

### 5. API Endpoint Mapping

Each gateway should implement the same API endpoints but with role-specific data:

```typescript
// Client Gateway API endpoints
GET /api/dashboard     // Client's personal dashboard data
GET /api/exercises     // Exercises assigned to this client
GET /api/assessments   // Assessments for this client

// Trainer Gateway API endpoints  
GET /api/exercises     // Exercises this trainer can assign
GET /api/assessments   // Assessments this trainer can create
GET /api/clients       // Clients assigned to this trainer

// Admin Gateway API endpoints
GET /api/exercises     // All exercises in the system
GET /api/assessments   // All assessments in the system
GET /api/clients       // All clients in the system
GET /api/trainers      // All trainers in the system
```

## Security Considerations

### 1. Token Security
- Access tokens expire in 1 hour
- Refresh tokens expire in 30 days
- Tokens are stored in localStorage (consider httpOnly cookies for production)
- Each gateway has separate client credentials

### 2. Route Protection
- Middleware validates tokens on every request
- Route access is checked against user role
- Automatic redirect to appropriate login

### 3. Data Gateway Isolation
- Each user role uses their own gateway for data
- Users can only access data they're authorized for
- Gateway-specific permissions are enforced
- Same API endpoints return different data based on user role

### 4. CORS Configuration
Each gateway must allow requests from the frontend domain:

```go
func enableCORS(w http.ResponseWriter) {
    w.Header().Set("Access-Control-Allow-Origin", "http://localhost:3000")
    w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}
```

## Deployment Considerations

### 1. Environment Configuration
- Set proper gateway URLs for production
- Use secure client secrets
- Configure CORS for production domain

### 2. Token Storage
- Consider using httpOnly cookies instead of localStorage
- Implement token rotation
- Add CSRF protection

### 3. Monitoring
- Log authentication attempts
- Monitor token usage
- Track gateway-specific metrics
- Monitor route access patterns

## Testing

### 1. Local Development
```bash
# Start all gateways
cd services/admin_gateway && go run cmd/server/main.go
cd services/trainer_gateway && go run cmd/server/main.go
cd services/client_gateway && go run cmd/server/main.go
cd services/organisation_gateway && go run cmd/server/main.go

# Start frontend
cd app && npm run dev
```

### 2. Test Scenarios
- Login with each gateway
- Test route access permissions
- Verify data comes from correct gateway based on user role
- Test gateway switching
- Access protected routes
- Token refresh
- Invalid token handling

## Future Enhancements

1. **Single Sign-On (SSO)**
   - Integrate with external identity providers
   - Support SAML/OIDC

2. **Role-Based Access Control (RBAC)**
   - Fine-grained permissions
   - Dynamic permission assignment

3. **Multi-Factor Authentication (MFA)**
   - TOTP support
   - SMS/email verification

4. **Audit Logging**
   - Authentication events
   - Permission changes
   - Gateway access logs
   - Route access patterns

5. **Caching Strategy**
   - Gateway-specific caching
   - Token caching
   - Data caching per gateway 