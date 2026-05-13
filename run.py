from app import create_app

# This creates the actual website application
app = create_app()

if __name__ == "__main__":
    # This starts the server so you can see it in your browser
    app.run(debug=True)