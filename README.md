# FitLife Hub

![FitLife Hub Banner](README-img/banner.jpg)

**FitLife Hub** is a full-stack Django e-commerce and fitness community platform. Users can shop for fitness products, subscribe to premium workout plans, track their progress, and engage with a supportive community.  
[Live Site Demo](https://fitlife-hub-22d9c7ccc31a.herokuapp.com/)

---

## Table of Contents

- [Project Purpose & Target Audience](#project-purpose--target-audience)
- [Features](#features)
- [Screenshots](#screenshots)
- [Data Schema](#data-schema)
- [Business Model](#business-model)
- [User Stories & Agile Process](#user-stories--agile-process)
- [UX Design & Wireframes](#ux-design--wireframes)
- [SEO & Marketing](#seo--marketing)
- [Testing](#testing)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Credits](#credits)

---

## Project Purpose & Target Audience

FitLife Hub is designed for fitness enthusiasts, beginners, and anyone seeking to improve their health through expert guidance and quality products.  
**Purpose:**  
- Provide a one-stop shop for fitness products and premium workout plans.
- Foster a supportive community for sharing progress and motivation.
- Enable users to track their fitness journey

---

## Features

- **E-commerce Store:** Browse and purchase fitness products.
- **Subscription Plans:** Subscribe to premium workout/nutrition plans.
- **User Authentication:** Secure registration, login, and profile management.
- **Role-Based Access:** Admin and member roles with tailored permissions.
- **Community Progress:** Share and view progress updates.
- **Product Reviews:** Leave and read reviews for products.
- **Newsletter Signup:** Stay updated with the latest offers and tips.
- **Responsive Design:** Mobile-friendly and accessible.
- **SEO Optimized:** Meta tags, sitemap, robots.txt, and canonical URLs.
- **Admin Dashboard:** Manage products, orders, users, and content.

---

## Screenshots

### Home Page
![Home Page](README-img/homepage.jpg)

### Product Detail
![Product Detail](README-img/product-detail.jpg)

### Subscription Plans
![Subscription Plans](README-img/subscriptions.jpg)

### Community Progress
![Community Progress](README-img/community.jpg)

### User Profile
![User Profile](README-img/profile.jpg)

---

## Data Schema

### Entity Relationship Diagram

[Click here to view the full Entity Relationship Diagram (PDF)](README-img/FitLife-Hub.pdf)

### Main Models

#### User & Profile
- **User:** Django’s built-in user model.
- **Profile:** Extends User with avatar, bio, and role (`member`, `admin`).

#### Product
- `name`, `description`, `price`, `image`, `stock`

#### Order & OrderItem
- **Order:** `user`, `created_at`, `status`, `total`
- **OrderItem:** `order`, `product`, `quantity`, `price`

#### Review
- `product`, `user`, `rating`, `comment`, `created_at`

#### Plan & Subscription
- **Plan:** `name`, `description`, `price`, `interval`
- **Subscription:** `user`, `plan`, `start_date`, `end_date`, `active`, `stripe_sub_id`

#### ProgressUpdate
- `user`, `title`, `content`, `image`, `created_at`

#### NewsletterSubscriber
- `email`, `subscribed_at`

---

## Business Model

FitLife Hub operates as a hybrid e-commerce and subscription platform:

- **Product Sales:** One-off purchases of fitness products.
- **Subscription Plans:** Recurring revenue from premium plans.
- **Community Engagement:** Drives retention and upselling.
- **Newsletter Marketing:** Builds brand loyalty and reach.

---

## User Stories & Agile Process

### Example User Stories

- As a user, I want to register and log in so I can access my profile and orders.
- As a user, I want to browse and purchase products securely.
- As a user, I want to subscribe to workout plans for ongoing guidance.
- As an admin, I want to manage products, orders, and users.

### Agile Board

![Agile Board Screenshot](README-img/agile-board.jpg)

- User stories, tasks, and sprints are tracked in [GitHub Projects](https://github.com/users/LNoonan3/projects/7).

---

## UX Design

### Design Process

- diagram was using dbdiagram
- Accessibility and mobile responsiveness were prioritized.
- User flows were tested and refined based on feedback.

## SEO & Marketing

- **Meta Tags:** All pages include descriptive meta titles and descriptions.
- **Canonical URLs:** Ensured for all main pages.
- **Sitemap:** [`sitemap.xml`](sitemap.xml) included for search engines.
- **robots.txt:** [`robots.txt`](robots.txt) controls crawler access.
- **404 Page:** Custom 404 with redirect options.
- **No Lorem Ipsum:** All content is meaningful and relevant.
- **Facebook Business Page:** [FitLife Hub on Facebook](https://www.facebook.com/fitlife.hub.25/)
- **Newsletter Signup:** Integrated on the homepage and footer.

---

## Testing

### Automated Testing

Automated tests are provided for all major components of the application:

- **Location of tests:**
  - `core/tests.py`
  - `store/tests.py`
  - `subscriptions/tests.py`
  - `users/tests.py`

- **Coverage:**
  - **Models:** Creation and validation of all main models (e.g., Product, Order, Plan, Subscription, Profile, ProgressUpdate, NewsletterSubscriber).
  - **Views:** Access control, CRUD operations, and correct template rendering for all main views.
  - **Forms:** Validation and submission for user profile, reviews, newsletter signup, etc.
  - **Authentication & Permissions:** Ensures only authorized users can access restricted views.

- **How to run the tests:**
  ```sh
  python manage.py test
  ```

- **Sample Output:**
  ```
  Found 17 test(s).
  Creating test database for alias 'default'...
  System check identified no issues (0 silenced).
  ..C:\Users\Lucy-Mai Noonan\OneDrive\Desktop\vscode-projects\FitLife-Hub-project5\.venv\Lib\site-packages\django\core\handlers\base.py:61: UserWarning: No directory at: C:\Users\Lucy-Mai Noonan\OneDrive\Desktop\vscode-projects\FitLife-Hub-project5\staticfiles\
    mw_instance = middleware(adapted_handler)
  ...............
  ----------------------------------------------------------------------
  Ran 17 tests in 26.338s

  OK
  Destroying test database for alias 'default'...
  ```

- **Example Test (from `store/tests.py`):**
  ```python
  def test_review_post(self):
      self.client.login(username='testuser', password='pass')
      url = reverse('store:product_detail', args=[self.product.pk])
      data = {'rating': 5, 'comment': 'Excellent!'}
      response = self.client.post(url, data)
      self.assertEqual(response.status_code, 302)
      review = Review.objects.get(product=self.product, user=self.user)
      self.assertEqual(review.rating, 5)
      self.assertEqual(review.comment, 'Excellent!')
  ```

### Manual Testing

- All CRUD actions tested for immediate UI reflection.
- Responsive design tested on Chrome, Firefox, Edge, and mobile devices.
- Accessibility checked with Lighthouse and manual keyboard navigation.

---

## Deployment

### Hosting

- Deployed on [Heroku](https://fitlife-hub-22d9c7ccc31a.herokuapp.com/)
- Static/media files managed via [AWS S3].

### Deployment Steps

1. Clone the repo:  
   `git clone https://github.com/yourusername/fitlife-hub.git`
2. Install dependencies:  
   `pip install -r requirements.txt`
3. Set environment variables (see `.env.example`).
4. Run migrations:  
   `python manage.py migrate`
5. Collect static files:  
   `python manage.py collectstatic`
6. Deploy to your platform (Heroku).

---

## Configuration

- **Procfile:** For Heroku deployment.
- **requirements.txt:** All dependencies listed.
- **env.py:** Environment variables (not committed).
- **settings.py:** Centralized configuration for database, static, and media files.

---

## Credits

- **Developed by:** Lucy-Mai Noonan
- **Icons:** [FontAwesome](https://fontawesome.com)
- **Images:** Unsplash, Pexels, and custom graphics.
- **Acknowledgements:** Code Institute, Django, Bootstrap.

---

![FitLife Hub Logo](README-img/logo.jpg)