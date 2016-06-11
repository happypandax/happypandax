>This cheat sheet can also be found in Happypanda `Settings -> About -> Regex Cheatsheet`

#### Characters I

Expression | Meaning 
----------|--------
. | Match any character except newline
^ | Match the start of the string
$ | Match the end of the string
*|Match 0 or more repetitions
+|Match 1 or more repetitions
?|Match 0 or 1 repetitions

#### Special Sequences I

Expression | Meaning 
----------|--------
\A|Match only at start of string
\b|Match empty string, only at beginning or end of a word
\B|Match empty string, only when it is not at beginning or end of word
\d|Match digits # same as [0-9]
\D|Match any non digit # same as [^0-9]

#### Characters II

Expression | Meaning 
----------|--------
*?|Match 0 or more repetitions non-greedy
+?|Match 1 or more repetitions non-greedy
??|Match 0 or 1 repetitions non-greedy
\ | Escape special characters
[]|Match a set of characters
[a-z]|Match any lowercase ASCII letter
[lower-upper]|Match a set of characters from lower to upper
[^]|Match characters NOT in a set
A\|B |Match either A or B regular expressions (non-greedy)

#### Special Sequences II

Expression | Meaning 
----------|--------
\s|Match whitespace characters # same as [ \t\n\r\f\v]
\S|Match non whitespace characters #same as [^ \t\n\r\f\v]
\w|Match unicode word characters # same as [a-zA-Z0-9_]
\W|Match any character not a Unicode word character # same as [^a-zA-Z0-9_]
\Z|Match only at end of string

#### Characters III

Expression | Meaning 
----------|--------
{m}|Match exactly m copies
{m,n}|Match from m to n repetitions
{,n}|Match from 0 to n repetitions
{m,}|Match from m to infinite repetitions
{m,n}?|Match from m to n repetitions non-greedy (as few as possible)

#### Groups I

Expression | Meaning 
----------|--------
(match)|Use to specify a group for which match can be retrieved later
(?:match)|Non-capturing version parenthesis (match cannot be retrieved later)
(?P<name>)|Capture group with name "name"
(?P=name)|Back reference group named "name" in same pattern
(?#comment)|Comment

#### Lookahead / Behind I

Expression | Meaning 
----------|--------
(?=match)|Lookahead assertion - match if contents matches next, but don't consume any of the string.
(?!match)|Negative lookahead assertion - match if contents do not match next
(?<=match)|Positive lookbehind assertion - match if current position in string is preceded by match
(?<!match)|Negative lookbehind assertion - match if current position is not preceded by match
(?(id/name)yes\|no)|Match "yes" pattern if id or name exists, otherwise match "no" pattern