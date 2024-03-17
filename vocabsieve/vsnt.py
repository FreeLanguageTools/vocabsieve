
FIELDS = ["Sentence", "Word", "Definition", "Definition#2", "Image", "Pronunciation"]


FRONT = '''<div class="widget front">

  <div class="title">What does this word mean here?</div>
  <div class="box targetLang">
    <div class="question">{{Sentence}}</div>
  </div>


  {{#Word}}<div class="box targetLang">
    <div class="question"><b>{{Word}}</b></div>
  </div>{{/Word}}


</div>
'''
BACK = '''{{FrontSide}}

<hr id=answer>

<div class="widget back">

		{{#Definition}}<div class="box nativeLang answer">{{Definition}}</div>{{/Definition}}

		{{#Definition#2}}<div class="box nativeLang answer">{{Definition#2}}</div>{{/Definition#2}}

	{{#Image}}<div class="image">{{Image}}</div>{{/Image}}

		{{#Pronunciation}}<div class="box targetLang">{{Pronunciation}}</div>{{/Pronunciation}}

{{#Tags}}<div class="tags">{{Tags}}</div>{{/Tags}}

</div>'''

CSS = '''.card {
  --bg-main-color: #f4f1de;
  --bg-title-color: #e07a5f;
	--bg-box-color: #8f5d5d;

	--targetLang-color: #9b2f40;
	--targetLang-font: sans-serif;
	--nativeLang-color: #3D405B;
	--nativeLang-font: sans-serif;

  --border-main-color: #8f5d5d;
  --border-box-color: #8f5d5d;

  --text-main-color: #eee5e9;
  --text-title-color: #ffffff;
  --text-box-color: #eee5e9;

  --alt-color: #9c5561;

  font-family: sans-serif,Menlo, Monaco;
  font-size: 1rem;
  background-color: var(--bg-main-color);
  color: var(--text-main-color);
  margin: 8px;
}

.hidden {
  display: none;
}

.mobile .card {
  margin: 0;
}

/*********** widget front back ****************/

.widget {
  position:relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.front {
  border-color: var(--border-main-color);
  border-style: solid;
  border-width: 4px 4px 0px 4px;
  border-radius: 16px 16px 0px 0px;
}

.back {
  border-color: var(--border-main-color);
  border-style: solid;
  border-width: 0px 4px 4px 4px;
  border-radius: 0px 0px 16px 16px;
  padding-bottom: 16px;
}

.mobile .front, .mobile .back {
  border: none;
}

/*********** title *******************/

.title {
  width: 100%;
  padding: 15px 0px;
  margin-bottom: 5px;
  font-style: normal;
	font-weight: bold;
}

.front .title {
  color: var(--text-title-color);
  background-color: var(--bg-title-color);
  border-radius: 12px 12px 0px 0px;
}

.back .title {
  color: var(--bg-title-color);
  background-color: var(--text-title-color);
}

.noteType {
  align-self: flex-end;
  margin-right: 1em;
  font-size: 0.7em;
	color: var(--border-main-color);
}

.mobile .noteType {
  display: none;
}

/******** image *******************/

.image {
  width: 300px; /* image max size */
  margin: 1em;
}

img {
  max-height: 100%;
  max-width: 100%;
  border-radius: 5px;
  box-shadow: rgba(50, 50, 93, 0.25) 0px 13px 27px -5px, var(--text-main-color) 0px 8px 16px -8px;
}

/******** elements styling *******************/
.box {
  color: var(--text-box-color);
  max-width: 60rem;
  align-items: center;
  margin: 0.3rem;
  padding: 0.7rem 1.2rem;
}


.targetLang {
	background-color: var(--targetLang-color);
	font-family: var(--targetLang-font);
}

.nativeLang {
	background-color: var(--nativeLang-color);
	font-family: var(--nativeLang-font);
}

.question {
  padding: 0rem 0.5rem;
  font-style: normal;
	font-size: 1.4em;
}

.answer {
  font-size: 1.2em;
  padding: .6rem 1rem;
  font-style: normal;
}

.bordered {
  border: 2px solid var(--border-box-color);
  border-width: 3px 2px 2px 3px;
  border-radius: 95% 3% 97% 3% / 4% 94% 3% 95%;
}

.alt-bordered {
  border: 2px solid var(--alt-color);
  border-width: 3px 4px 3px 3px;
  border-radius: 3% 97% 3% 97% / 97% 3% 97% 3%;
}

.replay-button svg {
  padding1: 0rem 1rem;
}

.replay-button svg path {
  stroke: white;
  fill: var(--alt-color);
}

.hint {
  font-size: 0.8rem;
  opacity: 0.6;
}

.hint a {
  color: var(--text-main-color);
  opacity: 0.6;
}

.notes {
  font-size: .8em;
  font-style: italic;
  padding1: 0rem 1.5rem;
  opacity: 0.8;
  display: flex;
  flex-direction: column;
}

.notes img  {
  width: 100px; /* notes image max size */
  margin: 1em;
}

.use {
  font-family: Helvetica Neue, Helvetica;
  font-size: 1.1em;
  font-style: normal;
  padding: 0rem 1.5rem;
}

.link {
	padding: .8rem 1rem;
  font-size: 10px;
	text-decoration: underline;
}
.tags {
    left: 10px;
    font-family: "Noto Sans", "Noto Sans CJK JP", "Liberation Sans", Arial, Sans, sans-serif;
    text-align: left;
    display: inline-block;
    text-transform: lowercase;
    background-color: #777;
    color: #fffaf0;
    font-weight: bold;
    padding: 1px 3px;
    margin: 0;
    cursor: pointer;
    border-radius: 3px;
    font-size: 12px;
    line-height: 14px;
}'''

CARDS = [
    {
        "Name": "Card 1",
        "Front": FRONT,
        "Back": BACK
    }
]
