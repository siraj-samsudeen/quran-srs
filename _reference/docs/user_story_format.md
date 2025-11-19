# Dev Checklist

## Step 1: User Story

- Given I am logged in, 
- When I add a product named 'Laptop' 
- Then 'Laptop' appears on my list of products

## Step 2: Data Model Changes

- Create `products` table 
   - name: Name of the product
   - user_id: ID of the user who added the product
   - Add unique index on (user_id, name) to prevent duplicates

## Step 3: Backend APIs

### `POST /products` : add new product for current user
- Validate product name is not empty
- user_id is automatically inferred based on the logged in credentials
- Prevent duplicate product names per user

### `GET /products` : list all products for current user
- Filter by current user's user_id

## Step 4: UI Interactions

- Product List Page: Displays the current user's list of products
- Add Product Form: Enables the user to add a new product

## Step 5: Unit/Integration Tests

- Create product with valid name -> Operation succeeds; product added
- Create product with empty name -> Operation fails; validation error
- Create product with duplicate name for same user -> Operation fails; duplicate error
- List products for user -> Only user's products returned
- Access product detail of another user's product -> Access denied or not found