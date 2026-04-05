import requests

class TelegramAlert:
    def __init__(self,token,chat_id):
        self.token=token
        self.chat_id=chat_id
        self.api_url=f"https://api.telegram.org/bot{self.token}/"

    def send_message(self,text):
        url=self.api_url+"sendMessage"
        params={"chat_id": self.chat_id, "text": text}
        return requests.get(url,params=params)
    
    def send_photo(self,photo_bytes,caption=""):
        url=self.api_url + "sendPhoto"
        files={"photo": ("incident.jpg", photo_bytes, "image/jpeg")}
        data = {"chat_id": self.chat_id, "caption": caption}
        return requests.post(url, files=files, data=data)
