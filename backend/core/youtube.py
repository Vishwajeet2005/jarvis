"""YouTube search — runs in cloud, no API key needed."""
import re, urllib.parse, urllib.request

def search(query: str, limit: int = 6) -> list:
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return [{"error": str(e)}]

    ids    = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"', html)
    chans  = re.findall(r'"ownerText":\{"runs":\[\{"text":"([^"]+)"', html)
    durs   = re.findall(r'"simpleText":"(\d+:\d+(?::\d+)?)"', html)

    results, seen = [], set()
    for i, vid in enumerate(ids):
        if vid in seen or len(results) >= limit: continue
        seen.add(vid)
        results.append({
            "id":       vid,
            "title":    titles[i] if i < len(titles) else "Unknown",
            "channel":  chans[i//2] if i//2 < len(chans) else "Unknown",
            "duration": durs[i] if i < len(durs) else "?",
            "url":      f"https://www.youtube.com/watch?v={vid}",
            "thumb":    f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
        })
    return results
