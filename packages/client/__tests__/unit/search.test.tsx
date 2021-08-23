import { replaceTextAtPosition } from '../../client/search_utils';

function extractCursor(text: string) {
  const t = text.replace('|', '');

  return {
    text: t,
    cursor: text.indexOf('|') + 1,
  };
}

function test(name, input, insert, expected, options?: any) {
  it(name, () => {
    const { text, cursor } = extractCursor(input);
    const r = replaceTextAtPosition(text, insert, cursor, {
      quotation: options.quotation !== undefined ? options.quotation : true,
    });

    // function R() {
    //     this.name = name
    //     this.success = r.text === expected
    //     this.input = input
    //     this.output = r.text
    //     this.expected = expected
    //     this.startPosition = r.startPosition
    //     this.endPosition = r.endPosition
    // }

    expect(r.text === expected);
  });
}

describe('Search', () => {
  describe('Search Completion', () => {
    test('end of single word', 'test|', 'yes', '"yes"');
    test('end of qouted single word', `'test'|`, 'yes', `'yes'`);
    test('first unbalanced quote mark', '"test yes|', 'no', '"no"');
    test('mid of single word', 'test|y', 'yes', '"yes"');
    test('mid of multi-word', 'yes test|y', 'no', 'yes "no"');
    test('mid of quotation multi-word', '"yes test|y', 'no', '"no"');
    test('beginning of quotation multi-word', '"yes |testy', 'no', '"no"');
    test('mid of balanced quote', '"test x|x"', 'yes', '"yes"');
    test(
      'mid of balanced quote 2',
      '"test x|x "no"',
      'yes',
      '"test "yes" "no"'
    );
    test(
      'end of multi-qoute words balanced',
      '"test" "two|',
      'yes',
      '"test" "yes"'
    );
    test(
      'end of multi-qoute words',
      '"test" "two| "ok"',
      'yes',
      '"test" "yes" "ok"'
    );
    test('end of qouted multi-word 2', `'test'| ok`, 'yes', `'yes' ok`);
    test('end of qouted multi-word 3', `"test"| ok`, 'yes', `"yes" ok`);
    test('end of qouted multi-word 4', `'test no'| ok`, 'yes', `'yes' ok`);
    test(
      'end of qouted multi-word 5',
      `"here" 'test no'| ok`,
      'yes',
      `"here" 'yes' ok`
    );
    test(
      'end of mixed qoutes multi-word',
      `"his sister's no" "two"|`,
      'test',
      `"his sister's no" "test"`
    );
    test(
      'end of mixed qoutes multi-word 2',
      `"his sister's no" "two" |`,
      'test',
      `"his sister's no" "two" "test"`
    );
    test(
      'mid of mixed qoutes multi-word',
      `"his 'fear |' no"`,
      'test',
      `"his 'test' no"`
    );
    test(
      'mid of mixed qoutes multi-word 2',
      `"his 'fear '| no"`,
      'test',
      `"his 'test' no"`
    );
    test('end of preceding space quotes', `'yes '|`, 'test', `'test'`);
    test(
      'end of preceding space quotes 2',
      `yes '| "hello"`,
      'test',
      `yes 'test' "hello"`
    );
    test(
      'already surrounded in qoutes 0',
      `hello |"test"`,
      '"test1"',
      `hello "test1" "test"`
    );
    test(
      'already surrounded in qoutes 1',
      `"test" |`,
      '"test1"',
      `"test" "test1"`
    );
    test('already surrounded in qoutes 2', `"test|"`, '"test1"', `"test1"`);
    test(
      'already surrounded in qoutes 3',
      `"test|"`,
      'test:"test1"',
      `test:"test1"`
    );
    test(
      'already surrounded in qoutes 4',
      `"test|"`,
      '"test":"test1"',
      `"test":"test1"`
    );
    test(
      'already surrounded in qoutes 5',
      `"test|"`,
      'test:test1',
      `"test:test1"`
    );
    test(
      'already surrounded in qoutes 6',
      `"test|"`,
      'test:"test1:yes"',
      `test:"test1:yes"`
    );
    test(
      'already surrounded in qoutes 7',
      `"test|"`,
      '"test":"test1:yes"',
      `"test":"test1:yes"`
    );
    test(
      'ambiguous apostrophes',
      "her sis' dog'|s 'frind' d",
      'test',
      "her sis' test 'frind' d",
      { quotation: false }
    );
    test(
      'ambiguous apostrophes 2',
      "her sis' dog|s 'frind' d",
      'test',
      "her sis' test 'frind' d",
      { quotation: false }
    );
    test(
      'ambiguous apostrophes 3',
      "her sis' dog|s' 'frind' d",
      'test',
      "her sis' test 'frind' d",
      { quotation: false }
    );
    test(
      'ambiguous apostrophes 4',
      "her sis' dogs' 'frind' d |",
      'test',
      "her sis' dogs' 'frind' d test",
      { quotation: false }
    );
    test(
      'ambiguous apostrophes 5',
      "got catch 'em| all, 'mon'",
      'test',
      "got catch test all, 'mon'",
      { quotation: false }
    );
    test('ambiguous apostrophes 6', "some 'x| test'", 'y', 'some y', {
      quotation: false,
    });
    test('plural possessive', "sis' f|riends' dog", 'test', "sis' test dog", {
      quotation: false,
    });
    test('plural possessive 2', "sis' |friends' dog", 'test', "sis' test dog", {
      quotation: false,
    });
    test('plural possessive 3', "sis' friends'| dog", 'test', "sis' test dog", {
      quotation: false,
    });
    test('plural possessive 4', "sisters' do|g", 'test', "sisters' test", {
      quotation: false,
    });
    test('plural possessive 5', "sisters ' do|g", 'test', 'sisters test', {
      quotation: false,
    });
    test('plural possessive 6', "'sisters ' do|g", 'test', "'sisters ' test", {
      quotation: false,
    });
    test(
      'plural possessive 7',
      "'sisters ' ' do|g",
      'test',
      "'sisters ' test",
      { quotation: false }
    );
    test('plural possessive 8', "sisters ' do|g", 'test', "sisters 'test'");

    test('exception for colon', `hello:world|`, 'test', `"test"`);
    test(
      'exception for colon 1',
      `"yes" hello|:"world"`,
      '"test"',
      `"yes" "test"`
    );

    test(
      'exception for colon 2',
      `"yes" hello:"world|"`,
      '"test"',
      `"yes" "test"`
    );
    test(
      'exception for colon 3',
      `"yes" hello|:"world"`,
      '"test"',
      `"yes" "test"`
    );
    test('exception for colon 4', `hello:"world|"`, 'test', `"test"`);
    test('exception for colon 5', `"hello":"world|"`, 'test', `"test"`);
    test('exception for colon 6', `"hello":"world"|`, 'test', `"test"`);
    test('exception for colon 7', `"hello":"world|"`, 'test', `test`, {
      quotation: false,
    });
    test('exception for colon 8', `"hello":"world"| ok`, 'test', `"test" ok`);
    test(
      'exception for colon 9',
      `"hello world":"ok ok"| ok`,
      'test',
      `"test" ok`
    );
    test(
      'exception for colon 10',
      `"hello |world":"ok ok" ok`,
      'test',
      `"test" ok`
    );
    test(
      'exception for colon 11',
      `"hello world":|"ok ok" ok`,
      'test',
      `"test" ok`
    );
    test('exception for colon 12', `"this : thing|"`, 'test', `"test"`);
    test('exception for colon 13', `"this 'other': thing|"`, 'test', `"test"`);
    test('exception for colon 14', `'this "other": thing|'`, 'test', `'test'`);
    test(
      'exception for colon 15',
      `hey:"other ok" |`,
      'test',
      `hey:"other ok" "test"`
    );
    test(
      'exception for colon 16',
      `ok |hey:"other ok" `,
      'lol:"yes yes"',
      `ok lol:"yes yes" hey:"other ok" `
    );
  });
});
