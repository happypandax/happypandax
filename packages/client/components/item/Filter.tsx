import classNames from 'classnames';
import Link from 'next/link';
import { Card, Checkbox, Grid, Label, List, Segment } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerFilter } from '../../misc/types';
import { urlstring } from '../../misc/utility';
import { LabelAccordion } from '../Misc';

export type FilterCardData = DeepPick<
  ServerFilter,
  'id' | 'name' | 'info' | 'filter' | 'enforce' | 'search_options'
>;

export const filterCardDataFields: FieldPath<ServerFilter>[] = [
  'name',
  'info',
  'filter',
  'enforce',
  'search_options',
];

export default function FilterCard({
  data,
  ...props
}: { data: FilterCardData } & React.ComponentProps<typeof Card>) {
  return (
    <Card {...props} className={classNames('horizontal', props.className)}>
      <Card.Content>
        <Card.Header>
          {data.name}
          <Label size="mini" className="right">
            {t`ID`}
            <Label.Detail>{data.id}</Label.Detail>
          </Label>
        </Card.Header>
        <Card.Meta>{data.info || t`No description`}</Card.Meta>
        <Card.Meta className="clearfix">
          <Label
            size="small"
            className="right"
            empty
            icon="refresh"
            title={t`Update`}
            as="a"
          />
          <Link href={urlstring('/library', { filter: data.id })} passHref>
            <Label
              size="small"
              empty
              className="right"
              icon="grid layout"
              title={t`Show galleries`}
              as="a"
            />
          </Link>
        </Card.Meta>
        <LabelAccordion label={t`Options`}>
          <Grid columns="equal">
            <Grid.Row>
              <Grid.Column>
                <List divided>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.enforce}
                      toggle
                      label={t`Enforce`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.case_sensitive'
                      )}
                      toggle
                      label={t`Case sensitive`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.match_all_terms'
                      )}
                      toggle
                      label={t`Match all terms`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.match_exact'
                      )}
                      toggle
                      label={t`Match terms exactly`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.children'
                      )}
                      toggle
                      label={t`Match on children`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.regex'
                      )}
                      toggle
                      label={t`Regex`}
                    />
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
