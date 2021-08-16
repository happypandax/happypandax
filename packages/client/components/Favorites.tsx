import { Divider, Grid, Header, Segment } from 'semantic-ui-react';

import t from '../misc/lang';
import { EmptySegment, TitleSegment } from './Misc';

// TODO; these should use metalists

export function SuggestedGalleries() {
  const galleries = [];
  return (
    <TitleSegment title={t`You may also love these`}>
      <Divider horizontal>
        <Header>{t`Galleries`}</Header>
      </Divider>
      {!galleries.length && <EmptySegment />}
      <Divider horizontal>
        <Header>{t`Artists`}</Header>
      </Divider>
      {!galleries.length && <EmptySegment />}
      <Divider horizontal>
        <Header>{t`Tags`}</Header>
      </Divider>
      {!galleries.length && <EmptySegment />}
    </TitleSegment>
  );
}

export function FavoriteGalleries() {
  const galleries = [];
  return (
    <TitleSegment title={t`Your Most Loved Galleries`}>
      {!galleries.length && (
        <EmptySegment description={`You don't have any favorited galleries`} />
      )}
    </TitleSegment>
  );
}

export function FavoriteCollections() {
  const collections = [];
  return (
    <TitleSegment title={t`Your Most Loved Collections`}>
      {!collections.length && (
        <EmptySegment
          description={`You don't have any favorited collections`}
        />
      )}
    </TitleSegment>
  );
}

export function FavoritePages() {
  const pages = [];

  return (
    <TitleSegment title={t`Your Most Loved Pages`}>
      {!pages.length && (
        <EmptySegment description={`You don't have any favorited pages`} />
      )}
    </TitleSegment>
  );
}

export function Favorites() {
  const artists = [];
  const tags = [];

  return (
    <Grid as={Segment} divided columns="equal">
      <Grid.Row>
        <Grid.Column>
          {!artists.length && (
            <EmptySegment
              description={`You don't have any favorited artists`}
            />
          )}
        </Grid.Column>
        <Grid.Column>
          {!tags.length && (
            <EmptySegment description={`You don't have any favorited tags`} />
          )}
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}

export function FavoritesMostRead() {
  const artists = [];
  const tags = [];

  return (
    <TitleSegment title={t`Your Most Read`}>
      <Grid as={Segment} divided columns="equal">
        <Grid.Row>
          <Grid.Column>
            {!artists.length && (
              <EmptySegment
                description={`You don't have any favorited artists`}
              />
            )}
          </Grid.Column>
          <Grid.Column>
            {!tags.length && (
              <EmptySegment description={`You don't have any favorited tags`} />
            )}
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </TitleSegment>
  );
}
