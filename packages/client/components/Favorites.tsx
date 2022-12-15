import { Divider, Grid, Header, Segment } from 'semantic-ui-react';

import t from '../client/lang';
import { EmptySegment, TitleSegment } from './misc';

// TODO; these should use metalists

export function Suggestions() {
  const galleries = [];
  return (
    <TitleSegment title={t`Check these out out`}>
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

export function TimeCapsuleGalleries() {
  const galleries = [];
  return (
    <TitleSegment title={t`Rekindle Your Love`}>
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

export function FavoriteArtistsMore() {
  const galleries = [];
  return (
    <TitleSegment title={t`More from artists you love`}>
      {!galleries.length && <EmptySegment />}
    </TitleSegment>
  );
}

export function FavoriteTagsMore() {
  const galleries = [];
  return (
    <TitleSegment title={t`More from tags you love`}>
      {!galleries.length && <EmptySegment />}
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
