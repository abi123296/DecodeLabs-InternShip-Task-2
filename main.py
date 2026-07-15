"""
main.py
-------
Movie Discovery API - a more modern take on Project 2.

Beyond basic CRUD, this API supports:
  - Filtering       GET /movies?genre=Sci-Fi&min_rating=7
  - Sorting         GET /movies?sort_by=rating
  - Pagination      GET /movies?page=1&limit=10
  - Recommendations GET /movies/{id}/recommendations
  - Stats           GET /stats
"""

from fastapi import FastAPI, HTTPException, Query, status
from typing import Optional
from models import Movie, MovieCreate, MovieUpdate

app = FastAPI(
    title="Movie Discovery API",
    description="Project 2 - Backend API Development (DecodeLabs)",
    version="1.0.0",
)

movies_db: list[dict] = []
next_id = 1


@app.get("/")
def root():
    return {"message": "Movie Discovery API is running. Visit /docs to try it out."}


# ---------------------------------------------------------------------
# GET /movies - list movies, with optional filtering/sorting/pagination
# ---------------------------------------------------------------------
@app.get("/movies", response_model=list[Movie])
def get_movies(
    genre: Optional[str] = Query(default=None, description="Filter by genre"),
    min_rating: Optional[float] = Query(default=None, ge=0, le=10, description="Only movies rated at least this"),
    watched: Optional[bool] = Query(default=None, description="Filter by watched status"),
    sort_by: Optional[str] = Query(default=None, description="Sort by 'rating' or 'year'"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=100, description="Movies per page"),
):
    results = movies_db

    # --- Filtering ---
    if genre:
        results = [m for m in results if m["genre"].lower() == genre.lower()]
    if min_rating is not None:
        results = [m for m in results if (m["rating"] or 0) >= min_rating]
    if watched is not None:
        results = [m for m in results if m["watched"] == watched]

    # --- Sorting ---
    if sort_by == "rating":
        results = sorted(results, key=lambda m: m["rating"] or 0, reverse=True)
    elif sort_by == "year":
        results = sorted(results, key=lambda m: m["year"], reverse=True)

    # --- Pagination ---
    start = (page - 1) * limit
    end = start + limit
    return results[start:end]


@app.get("/movies/{movie_id}", response_model=Movie)
def get_movie(movie_id: int):
    for movie in movies_db:
        if movie["id"] == movie_id:
            return movie
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")


# ---------------------------------------------------------------------
# GET /movies/{id}/recommendations - simple content-based suggestion
# ---------------------------------------------------------------------
@app.get("/movies/{movie_id}/recommendations", response_model=list[Movie])
def recommend_movies(movie_id: int, limit: int = Query(default=5, ge=1, le=20)):
    target = None
    for movie in movies_db:
        if movie["id"] == movie_id:
            target = movie
            break
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    # Score other movies by how many tags they share, plus same genre bonus
    scored = []
    for movie in movies_db:
        if movie["id"] == movie_id:
            continue
        shared_tags = len(set(movie["tags"]) & set(target["tags"]))
        genre_match = 1 if movie["genre"].lower() == target["genre"].lower() else 0
        score = shared_tags + genre_match
        if score > 0:
            scored.append((score, movie))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [movie for _, movie in scored[:limit]]


# ---------------------------------------------------------------------
# GET /stats - quick analytics over the whole watchlist
# ---------------------------------------------------------------------
@app.get("/stats")
def get_stats():
    if not movies_db:
        return {"total_movies": 0, "average_rating": None, "watched_count": 0, "genres": {}}

    rated = [m["rating"] for m in movies_db if m["rating"] is not None]
    genre_counts: dict[str, int] = {}
    for m in movies_db:
        genre_counts[m["genre"]] = genre_counts.get(m["genre"], 0) + 1

    return {
        "total_movies": len(movies_db),
        "average_rating": round(sum(rated) / len(rated), 2) if rated else None,
        "watched_count": sum(1 for m in movies_db if m["watched"]),
        "genres": genre_counts,
    }


# ---------------------------------------------------------------------
# POST /movies - create a new movie
# ---------------------------------------------------------------------
@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreate):
    global next_id

    for existing in movies_db:
        if existing["title"].lower() == movie.title.lower() and existing["year"] == movie.year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This movie already exists in your watchlist",
            )

    new_movie = movie.model_dump()
    new_movie["id"] = next_id
    movies_db.append(new_movie)
    next_id += 1
    return new_movie


@app.put("/movies/{movie_id}", response_model=Movie)
def update_movie(movie_id: int, update: MovieUpdate):
    for movie in movies_db:
        if movie["id"] == movie_id:
            update_data = update.model_dump(exclude_unset=True)
            movie.update(update_data)
            return movie
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")


@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int):
    for i, movie in enumerate(movies_db):
        if movie["id"] == movie_id:
            movies_db.pop(i)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
