import os
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from fastapi.responses import JSONResponse,FileResponse
import json
import networkx as nx
import matplotlib.pyplot as plt
from models import CR, Section, Specification, SpecVersion 
from schemas import QueryRequest

app= FastAPI()
DATABASE_URL = "mysql+mysqlconnector://root:pass..00@127.0.0.1:3306/3gpp_db"
engine = create_engine(DATABASE_URL)
SessionLocal= sessionmaker(autocommit=False,autoflush=False,bind=engine)
metadata = MetaData()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def similarity_search(query,df):
    documents = df['section_content'].tolist()
    documents.append(query)
    tfidf = TfidfVectorizer().fit_transform(documents)
    cosine_similarities = cosine_similarity(tfidf[-1],tfidf[:-1])
    similar_indices =cosine_similarities.argsort()[0][-5:][::-1]
    similarities= cosine_similarities[0,similar_indices]
    return df.iloc[similar_indices],similarities


def create_graph(query,results,similarities,db):
    G= nx.Graph()
    G.add_node("query",label=query)
    for idx, (result,similarity) in enumerate(zip(results.iterrows(),similarities)):
        section_id = result[1]['section_id']
        section_number = result[1]['section_number']
        version_id = result[1]['version_id']
        G.add_node(section_id,label=section_number)
        G.add_edge("query",section_id,weight=similarity,label=f"similarity {similarity:.2f}")
        # Add other relationships as edges here
        # Add CR nodes
        crs = db.query(CR).filter(CR.clauses_affected.contains(section_id)).all()
        for cr in crs:
            cr_id = cr.cr_id
            meeting_number = cr.meeting_number
            source_to_WG = cr.source_to_WG
            G.add_node(cr_id, label=f"CR {cr.cr_number}")
            G.add_edge(section_id, cr_id, label="affects")
            # Add meeting number node
            if meeting_number:
                G.add_node(meeting_number, label=f"Meeting {meeting_number}")
                G.add_edge(cr_id, meeting_number, label="discussed at")
                 # Add source_to_WG node
            if source_to_WG:
                G.add_node(source_to_WG, label=f" {source_to_WG}")
                G.add_edge(cr_id, source_to_WG, label="created by")
        
        spec_version = db.query(SpecVersion).filter(SpecVersion.version_id == version_id).first()
        if spec_version:
            spec_id = spec_version.spec_id
            spec = db.query(Specification).filter(Specification.spec_id == spec_id).first()
            if spec:
                G.add_node(spec.spec_id, label=spec.spec_number)
                G.add_edge(section_id, spec.spec_id, label="part of")
        
            
       

        
    return G

@app.post('/search')
async def search(request: QueryRequest, db: Session = Depends(get_db)):

    # Build the query with optional filters
    query= db.query(Section)
    if request.spec_number:
        query=query.join(SpecVersion).join(Specification).filter(Specification.spec_number==request.spec_number)
    if request.version_number:
        query=query.filter(SpecVersion.version_number==request.version_number)
    if request.section_number:
        query=query.filter(Section.section_number==request.section_number)
    #  load the filterd data into a DataFrame
    df = pd.read_sql(query.statement,db.bind)

    if df.empty:
        return JSONResponse(content={"message": "No matching records found."},status_code=404)
    # Perform similarity search
    results,similarities=similarity_search(request.query,df)

    if results.empty:
        return JSONResponse(content={"message": "No similar documents found."}, status_code=404)
    # Create graph
    graph = create_graph(request.query, results,similarities,db)
    # Convert graph to node-link data
    graph_data=nx.node_link_data(graph)
    # Return the graph data as JSON
    #return JSONResponse(content=json.dumps(graph_data))
 # Draw and save the graph
    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(graph)
    edge_labels = nx.get_edge_attributes(graph, 'label')
    nx.draw(graph, pos, with_labels=True, node_size=7000, node_color='lightblue', font_size=20, font_weight='bold', font_color='black')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels,font_size=15,)
    graph_image_path = "graph.png"
    plt.savefig(graph_image_path,format="PNG")
    plt.close()
    if os.path.exists(graph_image_path):
        return FileResponse(graph_image_path)
    else:
        return JSONResponse(content={"message": "Failed to generate graph image."}, status_code=500)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=8000)