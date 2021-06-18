from Main import app, PORT, TOKEN, updater


if __name__ == "__main__":
    app.run()
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url="https://groupify-orbital.herokuapp.com/" + TOKEN)
    updater.idle()