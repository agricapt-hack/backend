import youtubesearchpython

class YTService:
    def search(self, query, max_results=3):
        videos_search = youtubesearchpython.VideosSearch(query, limit=max_results)
        results = []
        for item in videos_search.result().get("result", []):
            results.append(item)
        return results
    

YTSERVICE_HANDLER = YTService()