### {{ word }}
#### Pronunciation
- US: {{ american_ipa }}
- UK: {{ british_ipa }}
#### Explanation
{% for meaning in meanings %}
##### {{ meaning.part_of_speech }}
- {{ meaning.explanation }}
{% endfor %}
#### Example sentence
{% for meaning in meanings %}
##### {{ meaning.part_of_speech }}
{% for example in meaning.examples %}
- {{ example.english }}
{% endfor %}
{% endfor %}
#### Synonyms
{% for meaning in meanings %}
- {{ meaning.synonyms | join(", ") }}
{% endfor %}
#### Derived forms
{% for form in derived_forms %}
- {{ form }}
{% endfor %}
#### Related word partners
{% for partner in related_word_partners %}
- {{ partner }}
{% endfor %}
