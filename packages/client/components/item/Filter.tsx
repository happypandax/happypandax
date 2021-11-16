import classNames from 'classnames';
import { Card, Checkbox, Grid, Label, List, Segment } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerFilter } from '../../misc/types';
import { LabelAccordion } from '../Misc';

export type FilterCardData = DeepPick<
  ServerFilter,
  'id' | 'name' | 'info' | 'filter'
>;

export const filterCardDataFields: FieldPath<ServerFilter>[] = [
  'name',
  'info',
  'filter',
];

export default function FilterCard({ data }: { data: FilterCardData }) {
  return (
    <Card className={classNames('horizontal')}>
      <Card.Content>
        <Card.Header>
          {data.name}
          <Label size="mini" className="right">
            {t`ID`}
            <Label.Detail>{data.id}</Label.Detail>
          </Label>
        </Card.Header>
        <Card.Meta>{data.info || t`No description`}</Card.Meta>
        <LabelAccordion label={t`Options`}>
          <Grid columns="equal">
            <Grid.Row>
              <Grid.Column>
                <List divided>
                  <List.Item>
                    <Checkbox toggle label={t`Enforce`} />
                  </List.Item>
                  <List.Item>
                    <Checkbox toggle label={t`Case sensitive`} />
                  </List.Item>
                  <List.Item>
                    <Checkbox toggle label={t`Match all terms`} />
                  </List.Item>
                  <List.Item>
                    <Checkbox toggle label={t`Match terms exactly`} />
                  </List.Item>
                  <List.Item>
                    <Checkbox toggle label={t`Match on children`} />
                  </List.Item>
                  <List.Item>
                    <Checkbox toggle label={t`Regex`} />
                  </List.Item>
                </List>
              </Grid.Column>
              <Grid.Column>
                {!!data.filter && (
                  <Card.Description
                    as={Segment}
                    tertiary
                    className={classNames('small-padding-segment')}>
                    {data.filter}
                  </Card.Description>
                )}
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </LabelAccordion>
      </Card.Content>
    </Card>
  );
}
