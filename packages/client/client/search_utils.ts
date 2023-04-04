const defaultMarks = ['"', "'"];

function searchForBreaks({
  oldText,
  processedText,
  leftPosition,
  rightPosition,
  leftBalanced,
  rightBalanced,
  rightMark,
  leftMark,
  leftUnbalancedMark,
  rightUnbalancedMark,
}) {
  let rightSearchBreak = NaN;
  let leftSearchBreak = NaN;
  let inColon = false;

  const leftSearchPosition = Math.min(leftPosition + 1, processedText.length);

  if (!leftBalanced) {
    // search for the break to the right of the cursor

    for (let s of [' ']) {
      let searchBreakCandidate = processedText.slice(rightPosition).search(s);
      if (
        (isNaN(rightSearchBreak) || searchBreakCandidate < rightSearchBreak) &&
        searchBreakCandidate > -1
      )
        rightSearchBreak = searchBreakCandidate;
    }

    // search for the break to the left of the cursor

    if (!rightBalanced || !rightMark) {
      const leftMarks = leftUnbalancedMark
        ? [leftUnbalancedMark]
        : defaultMarks;
      const rightMarks = rightUnbalancedMark
        ? [rightUnbalancedMark]
        : defaultMarks;

      // both left and right hand sides are unbalanced, so the cursor is either in the middle of a
      // balanced quote, or at the end of one -- `" 'sisters'| friend"` or `'sis|ters'`
      //if the cursor is at the end of a balanced quote

      if (
        rightPosition - 1 > 0 &&
        !rightMarks.includes(processedText[rightPosition - 1])
      ) {
        rightSearchBreak = processedText.length;
        // replace the entirety of the balanced quote
        for (let s of rightMarks) {
          let searchBreakCandidate = processedText
            .slice(rightPosition)
            .search(s);
          if (
            (isNaN(rightSearchBreak) ||
              searchBreakCandidate < rightSearchBreak) &&
            searchBreakCandidate > -1
          )
            rightSearchBreak = searchBreakCandidate + 1;
        }
      }

      // search on the left side
      for (let s of leftMarks) {
        let searchBreakCandidate = processedText
          .slice(0, leftPosition)
          .lastIndexOf(s);
        if (
          (isNaN(leftSearchBreak) || searchBreakCandidate > leftSearchBreak) &&
          searchBreakCandidate > -1
        ) {
          const markPos = Math.max(searchBreakCandidate - 1, 0);
          if (oldText[markPos] === ':') {
            // we're in a colon word
            leftSearchBreak = NaN;
            inColon = true;
          } else {
            leftSearchBreak = searchBreakCandidate;
          }
        }
      }

      // it found a break, make sure it's actually considered a break, eg. "sister' ok| 'yes'" -> "sister' "test" 'yes'"
      if (!isNaN(leftSearchBreak)) {
        const before = Math.max(
          Math.min(leftSearchBreak - 1, leftPosition - 1),
          0
        );
        const after = Math.max(Math.min(leftSearchBreak + 1, rightPosition), 0);
        if (processedText[before] !== ' ' && processedText[after] === ' ') {
          // if not then just break at nearest whitespace
          const searchBreakCandidate = processedText
            .slice(0, leftPosition + 1)
            .lastIndexOf(' ');
          leftSearchBreak =
            searchBreakCandidate > -1 ? searchBreakCandidate : NaN;
        }
      }
    }
  }

  // handle whitespace here
  if (leftBalanced || inColon || (rightMark && rightBalanced)) {
    if (oldText[leftSearchPosition] === ' ') {
      console.log('setting: ', leftPosition);
      leftSearchBreak = leftPosition;
    } else if (isNaN(leftSearchBreak)) {
      let searchBreakCandidate = processedText
        .slice(0, leftSearchPosition)
        .lastIndexOf(' ');
      if (searchBreakCandidate !== -1) {
        leftSearchBreak = searchBreakCandidate;
      }
    }

    console.log('start: ', [
      leftSearchBreak,
      oldText.length,
      oldText[leftSearchPosition],
    ]);

    // for the right hand side, default is end of text
    rightSearchBreak = processedText.slice(
      Math.max(rightPosition - 1, 0)
    ).length;
    let rightSearchBreakCandidate = processedText
      .slice(Math.max(rightPosition - 1, 0))
      .search(' ');
    if (
      isNaN(rightSearchBreak) ||
      (rightSearchBreakCandidate < rightSearchBreak &&
        rightSearchBreakCandidate != -1)
    ) {
      rightSearchBreak = rightSearchBreakCandidate;
    }

    if (
      (oldText[leftPosition] === ' ' || leftPosition === 0) &&
      leftBalanced &&
      rightBalanced
    ) {
      rightSearchBreak = 1;
    }
  }

  // handle when end-quote is followed by cursor, then it should replace the whole quoted text
  const markPos = Math.max(leftSearchPosition - 1, 0);

  if (defaultMarks.includes(processedText[markPos])) {
    if (leftUnbalancedMark !== processedText[markPos]) {
      const r = processedText
        .slice(0, markPos)
        .lastIndexOf(processedText[markPos]);
      const markPos2 = r - 1;
      // need to make sure we don't include a quote not considered part of this text
      if (markPos2 < 0 || processedText[markPos2] === ' ') {
        if (r !== -1) {
          leftSearchBreak = r;
          rightSearchBreak = 0;
        } else {
          leftSearchBreak = leftPosition;
        }
      }
    }
  }
  console.log('end: ', [leftSearchBreak, rightSearchBreak]);

  return {
    rightSearchBreak,
    leftSearchBreak,
  };
}

function isTextBalanced({ text }) {
  let stack = [];
  let balanced = true;
  let firstUnbalancedMark;
  let lastUnbalancedMark;
  let mark = false;
  let firstMarkType;
  let lastMarkType;

  const nonApostrophe = `:(){}|/\\^!@#\$%%^&*-=+~[]<>? `.split('');
  for (let i = 0; i < text.length; i++) {
    if (defaultMarks.includes(text[i])) {
      const c = text[i];

      // skip if between characters
      // this is for an edge case where words have apostrophes: "brother's and sisters'" but this is not skipped: "sisters' and"
      if (
        i > 0 &&
        !nonApostrophe.includes(text[i - 1]) &&
        i < text.length - 1 &&
        !nonApostrophe.includes(text[i + 1])
      ) {
        continue;
      }

      if (firstMarkType) {
        firstMarkType = c;
      } else {
        lastMarkType = c;
      }

      if (stack.length && stack[stack.length - 1] === c) {
        stack.pop();
      } else {
        mark = true;
        stack.push(c);
      }
    }
  }

  // if there's only one quote type, both first and last are it
  if (!lastMarkType) {
    lastMarkType = firstMarkType;
  }

  balanced = !stack.length;

  // if not balanced, save the misbalanced marks
  if (!balanced) {
    firstUnbalancedMark = stack[stack.length - 1];
    lastUnbalancedMark = stack[0];
  }
  return {
    balanced,
    mark,
    firstMarkType,
    lastMarkType,
    firstUnbalancedMark,
    lastUnbalancedMark,
  };
}

export function replaceTextAtPosition( //can you see this?
  oldText,
  text,
  position,
  { quotation = true, addSpace = false }
) {
  // the index of the character to the left of caret
  const leftPosition = Math.max(position - 2, 0);
  // the index of the character to the right of caret
  const rightPosition = Math.max(position - 1, 0);

  // substitute placeholders for patterns with colon to enable entity-stringing
  // i.e. "asdf":"qwer" becomes "asdf___qwer", foo:"bar" becomes foo___bar", etc
  const processedText = oldText.replace(/["|']:["|']/g, '___');

  const leftText = processedText.slice(0, leftPosition + 1);
  const rightText = processedText.slice(rightPosition, processedText.length);
  console.log([leftText, rightText]);
  const {
    balanced: leftBalanced,
    mark: leftMark,
    lastMarkType: leftQuoteType,
    firstUnbalancedMark: leftUnbalancedMark,
  } = isTextBalanced({ text: leftText });

  const {
    balanced: rightBalanced,
    mark: rightMark,
    firstMarkType: rightQuoteType,
    lastUnbalancedMark: rightUnbalancedMark,
  } = isTextBalanced({ text: rightText });

  let startPosition = 0;
  let endPosition = oldText.length;

  const { leftSearchBreak, rightSearchBreak } = searchForBreaks({
    oldText,
    processedText,
    leftPosition,
    rightPosition,
    leftBalanced,
    rightBalanced,
    rightMark,
    leftMark,
    leftUnbalancedMark,
    rightUnbalancedMark,
  });

  // did we find any breaks, if so, set range
  if (!isNaN(leftSearchBreak)) {
    startPosition = leftSearchBreak;
  }

  if (!isNaN(rightSearchBreak)) {
    endPosition = rightPosition + rightSearchBreak;
  }
  // the text we want to insert
  let t = text;

  // add quotes if necessary
  if (quotation) {
    let qouteType = leftUnbalancedMark
      ? leftUnbalancedMark
      : rightUnbalancedMark
      ? rightUnbalancedMark
      : '';

    // as an exception, if a qoute is touching the cursor to the left, use that
    // quote's quote mark instead
    if (defaultMarks.includes(leftText[leftText.length - 1])) {
      qouteType = leftText[leftText.length - 1];
    }

    if (!qouteType) {
      // check if quote types match
      if (leftQuoteType === rightQuoteType && leftQuoteType) {
        qouteType = leftQuoteType;
      } else if (leftQuoteType) {
        // otherwise, check if there is left quote
        qouteType = leftQuoteType;
      } else if (rightQuoteType) {
        // otherwise, use right quote
        qouteType = rightQuoteType;
      }
    }

    qouteType = ['"', "'"].includes(qouteType) ? qouteType : '"';

    // check if text is already surrounded by qoutes
    const leftQouted = ['"', "'"].map((q) => t.search(q) === 0);
    const rightQouted = ['"', "'"].map(
      (q) => t.lastIndexOf(q) === t.length - 1
    );
    const zip = (rows) => rows[0].map((_, c) => rows.map((row) => row[c]));

    // we dont want to qoute `hello:"world"`
    const colonQuoted = t.search(':') !== -1 && rightQouted.some(Boolean);

    if (
      !colonQuoted &&
      !zip([leftQouted, rightQouted])
        .map((a) => a.every(Boolean))
        .some(Boolean)
    ) {
      t = qouteType + t + qouteType;
    }
  }

  // add space around new text if needed
  if (startPosition - 1 > 0 && oldText[startPosition - 1] !== ' ') {
    t = ' ' + t;
  }
  if (oldText[endPosition] !== ' ') {
    t = t + ' ';
  }

  const newEndPosition = startPosition + t.length;

  // we got the range, now insert the new text at range by splicing, we don't need to consider whether
  // we're replacing or inserting because we're working purely with the range
  const newText =
    oldText.slice(0, startPosition) + t + oldText.slice(endPosition);

  return {
    text: newText,
    startPosition,
    endPosition,
    newEndPosition,
  };
}
