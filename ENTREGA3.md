# Deliverable 3 – Choosy Web Application (Web 3.0 / RDFa)

## 1. GitHub Repository

**URL:** https://github.com/choosy-friends-app/choosy-app

Branch for this deliverable: `assigment-3`

## 2. Web 3.0 Feature: RDFa Semantic Markup

### Entity selected: Plan (Activity option)

The entity chosen for semantic markup is the **Plan** model, which represents a concrete activity option that a group of friends votes on (e.g., "Dinner at Nomo", "Hiking trail at Collserola"). It is the central domain object of the Choosy application.

### Schema.org type used: `schema:Event`

A `Plan` is mapped to **`schema:Event`** because it models a concrete activity with a date, location, price, duration and participants – exactly what the schema.org Event type describes.

#### Properties mapped

| Model field         | schema.org property                    | Notes |
|---------------------|----------------------------------------|-------|
| `title`             | `schema:name`                          | Main name of the event |
| `description`       | `schema:description`                   | Short description |
| `scheduled_for`     | `schema:startDate`                     | ISO 8601 datetime on `<time>` element |
| `duration_minutes`  | `schema:duration`                      | Converted to ISO 8601 duration (PTxHyM) via `<meta>` |
| `price`             | `schema:offers / schema:Offer / schema:price` | Nested Offer entity with `priceCurrency="EUR"` and `availability=InStock` |
| `place_name`        | `schema:location / schema:Place / schema:name` | Nested Place entity |
| `address`           | `schema:location / schema:Place / schema:address / schema:PostalAddress / schema:streetAddress` | Nested PostalAddress inside Place |
| `image_url`         | `schema:image`                         | `<img property="image">` |
| `group.name`        | `schema:organizer / schema:Organization / schema:name` | The group that organises the activity |
| `tag`               | `schema:keywords`                      | Activity category tag |
| *(fixed)*           | `schema:eventStatus`                   | `schema:EventScheduled` |
| *(fixed)*           | `schema:eventAttendanceMode`           | `schema:OfflineEventAttendanceMode` |

The resulting nesting (Event → Place → PostalAddress, Event → Offer) provides a data structure at least as rich as the `PostalAddress` or `Review` examples from the course tutorial.

### New URL and view

| Resource | URL | View |
|----------|-----|------|
| Plan detail (RDFa) | `/plan/<pk>/` | `core.web.plans.plan_detail` |

Access is restricted to authenticated users who are active members of the plan's group.

### Where to find the markup

File: `front/templates/pages/plan_detail.html`

The `<article>` element that wraps the whole page carries `vocab="https://schema.org/"` and `typeof="Event"`, making every child `property="…"` attribute resolve against the schema.org vocabulary without any prefix. This is the same approach shown in the Django Web 3.0 RDFa Tutorial.

### Validation

The HTML output of `/plan/<pk>/` can be tested at **https://validator.schema.org** by pasting the rendered HTML. It will detect the `Event` entity with its nested `Offer`, `Place` and `PostalAddress` entities.

## 3. Changes compared to Deliverable 2

* **No model changes** were required. The `Plan` model already contained all the fields needed for the RDFa markup (`price`, `duration_minutes`, `place_name`, `address`, `scheduled_for`, `image_url`, `tag`).
* **New view** `plan_detail` added to `core/web/plans.py` (permission-guarded, converts `duration_minutes` to ISO 8601 format before passing it to the template).
* **New URL** `plan/<int:pk>/` registered in `core/urls.py` with name `plan_detail`.
* **New template** `front/templates/pages/plan_detail.html` with full RDFa markup.
* **Link added** in `front/templates/pages/active_plans.html`: plan titles in the Live Progress section now link to the plan detail page.
