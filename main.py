import uvicorn
def main():
    uvicorn.run("src.api.app:fastapi_app", host="0.0.0.0", port=8000, reload=True)
    
    

if __name__ == "__main__":
    main()
