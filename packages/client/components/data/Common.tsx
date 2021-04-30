import { Label, Icon, Table, Header } from 'semantic-ui-react';
import t from '../../misc/lang';

export function LanguageLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label color="blue" basic {...props}>
      <Icon className="globe africa" />
      {!props.children && 'English'}
      {props.children}
    </Label>
  );
}

export function ReadCountLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Timed read`} color="blue" basic {...props}>
      <Icon className="book open" />
      23
    </Label>
  );
}

export function PageCountLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Page count`} color="blue" basic {...props}>
      <Icon name="clone outline" />
      19
    </Label>
  );
}

export function StatusLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Status`} color="blue" basic {...props}>
      <Icon name="calendar check" />
      Ongoing
    </Label>
  );
}

export function GroupingNumberLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Number`} color="blue" basic {...props}>
      1
    </Label>
  );
}

export function DateAddedLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Date added`} {...props}>
      {t`Added`}
      <Label.Detail>12 March</Label.Detail>
    </Label>
  );
}

export function LastReadLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Last read`} {...props}>
      {t`Read`}
      <Label.Detail>12 March</Label.Detail>
    </Label>
  );
}

export function LastUpdatedLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Last updated`} {...props}>
      {t`Updated`}
      <Label.Detail>12 March</Label.Detail>
    </Label>
  );
}

export function DatePublishedLabel(props: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Date published`} {...props}>
      {t`Published`}
      <Label.Detail>12 March</Label.Detail>
    </Label>
  );
}

export function TitleTable() {
  const titles = [
    { language: 'English', title: 'Item Title' },
    { language: 'Japanese', title: 'Item Alternative Title' },
    { language: 'Russian', title: 'Item Alternative Title 2' },
  ];

  const primary = titles[0];
  const altTitles = titles.filter((v) => v !== primary);

  return (
    <Table basic="very" compact="very" verticalAlign="middle">
      <Table.Row>
        <Table.Cell colspan="2" textAlign="center">
          <GroupingNumberLabel
            className="float-left"
            circular
            size="tiny"
            color="black"
          />
          <Label size="tiny" className="float-right">
            {t`ID`}
            <Label.Detail>1234</Label.Detail>
          </Label>
          <div>
            <Header size="medium">{primary.title}</Header>
          </div>
        </Table.Cell>
      </Table.Row>
      {altTitles.map((v) => (
        <Table.Row key={v.id ?? v.title} verticalAlign="middle">
          <Table.Cell collapsing>
            <LanguageLabel color={undefined} basic={false} size="tiny">
              {v.language}
            </LanguageLabel>
          </Table.Cell>
          <Table.Cell>
            <Header size="tiny" className="sub-text">
              {v.title}
            </Header>
          </Table.Cell>
        </Table.Row>
      ))}
    </Table>
  );
}
