---
description: check the word meanings and find out scarce meaning of a word if any. $ARG
---
帮我检查一下这个文件 $ARG 里面， 每个单词所对应的多个meaning (即meaning[id]['explanation'])，判断一下有没有哪个meaning其实是这个词汇所对应的非常不常见的含义，或者是非常不常见的part of speech。帮我把你找到的所有的这些你认为不常见的词的meaning都列出来(切记不要修改这个原始文件)。具体的判断准则请参考以下介绍：

These must be natural, high-frequency phrases or patterns that people actually use in daily English. They should help learners know how to use the word in real sentences.

Meaning Selection Policy:
  - Only include meanings and parts of speech that are common, current, and useful in modern everyday English or standard school-level English. Do not include archaic, literary, historical, highly technical, dictionary-only, or extremely rare meanings, even if they exist in a dictionary.
  - Do not generate a second meaning just to fill the quota. If the word has only one common modern meaning, generate only one meaning.
  - A meaning is suitable only if an ordinary educated native English speaker would likely recognize it and find it natural in normal reading, conversation, schoolwork, or common media.
  - Avoid rare part-of-speech conversions. For example, do not include a verb meaning just because a noun can technically be used as a verb, unless that verb use is common in modern English.
  - If the input word has a homograph with a different pronunciation and unrelated meaning, do not mix it into the same entry unless it is clearly one of the most common modern uses of that spelling. For example, for “wound” as /wuːnd/, do not include “wound” as the past tense of “wind” /waʊnd/.
