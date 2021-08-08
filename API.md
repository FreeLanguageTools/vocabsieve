# Local API for ssmtool
The default API is at http://127.0.0.1:39284, but this can be changed by the user.

## Endpoints
| Verb | Path | Usage |
-------|-------|--------
GET | `/healthcheck` | Check if API is online
GET | `/version` | Get the version of API running. The current version is 1, which is the only possible value now.
GET | `/define/<word>` | Get the definition of a word. The response is a [definition item](#definition-item). Lemmatization depends on user setting.
GET | `/define/<word>?lemmatize=false` | Get the definition of a word regardless of user settings without lemmatization.
GET | `/lemmatize` | Get the lemmatized form of a word. Response is a simple string.
GET | `/logs` | Get the full database containing all past lookups and note creations
GET | `/stats` | Get data about lookups and new cards today
POST| `/translate?src=<lang>&dst=<lang>` | Translate text through Google Translate with specified source and destination languages in ISO 639-1 format. Both are query parameters are optional and user settings will be used if not specified. No API key required. Request body should be a json object with text in the "text" field. Response is a [translation item](#translation-item).
POST | `/createNote` | The request body should be a [note item](#note-item).

## Data formats
### Definition item
Depending on whether the user has a second dictionary source enabled, it can be either:
```json
{
    "word": "blue",
    "definition": "a color..."
}
```
or
```json
{
    "word": "blue",
    "definition": "a color...",
    "definition2": "azúl"
}
```
### Note item
```json
{
    "sentence": "The quick brown fox jumps over the lazy dog.",
    "word": "fox",
    "definition": "an animal..",
    "tags": []
}
```
Please note that even with `tags` being an empty array, the default tags specified in ssmtool config will still be added.

Using two definitions is not yet supported, and neither are audio and image data, but they are expected to be added in the future as optional fields in base64 format or as file paths. 

### Translation item
```json
{
    "src": "ru",
    "dst": "en",
    "translation": "This is a book"
}
```
The `src` and `dst` fields are always present regardless of whether they are specified in URL query parameters. When not specified they represent user settings.