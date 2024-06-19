import nest_asyncio
from fastapi import FastAPI, HTTPException, Query, Path
from typing import List, Optional
from pydantic import BaseModel
from pymongo import MongoClient

nest_asyncio.apply()

class Review(BaseModel):
    reviewer: str
    comment: str
    rating: int

class Protein(BaseModel):
    protein_id: str
    name: str
    sequence: str
    length: int
    organism: str
    function: str
    reviews: Optional[List[Review]] = []

client = MongoClient('localhost', 27017)
db = client['protein']
collection = db['protein_info']

app = FastAPI(title="Protein Information API")

# Define the endpoints
@app.get("/protein/{protein_id}", response_model=Protein)
async def get_protein_by_id(protein_id: str = Path(..., description="The ID of the protein to retrieve", examples="P12345")):
    try:
        protein = collection.find_one({"protein_id": protein_id})
        if protein:
            return protein
        raise HTTPException(status_code=404, detail="Protein not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proteins/organism/{organism}", response_model=List[Protein])
async def get_proteins_by_organism(organism: str = Path(..., description="The organism to retrieve proteins from", examples="Homo sapiens")):
    try:
        cursor = collection.find({"organism": organism})
        proteins = await cursor.to_list(length=None)  # No limit specified
        if proteins:
            return proteins
        raise HTTPException(status_code=404, detail="Proteins not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proteins/top-rated", response_model=List[Protein])
async def get_top_proteins_by_rating(limit: int = Query(10, description="Number of top proteins to retrieve based on review rating", examples=10)):
    try:
        cursor = collection.aggregate([
            {"$addFields": {"average_rating": {"$avg": "$reviews.rating"}}},
            {"$sort": {"average_rating": -1}},
            {"$limit": limit}
        ])
        top_proteins = await cursor.to_list(length=limit)
        if top_proteins:
            return top_proteins
        raise HTTPException(status_code=404, detail="Proteins not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
