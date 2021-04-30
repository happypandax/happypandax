import { Segment, Header, Grid } from 'semantic-ui-react';
import t from '../misc/lang';
import { EmptyMessage, TitleSegment } from './Misc';

export function FavoriteGalleries() {
  const galleries = [];
  return (
    <TitleSegment title={t`Galleries`}>
      {!galleries.length && (
        <EmptyMessage description={`You don't have any favorited galleries`} />
      )}
    </TitleSegment>
  );
}

export function FavoriteCollections() {
  const collections = [];
  return (
    <TitleSegment title={t`Collections`}>
      {!collections.length && (
        <EmptyMessage
          description={`You don't have any favorited collections`}
        />
      )}
    </TitleSegment>
  );
}

export function FavoritePages() {
  const pages = [];

  return (
    <TitleSegment title={t` Pages`}>
      {!pages.length && (
        <EmptyMessage description={`You don't have any favorited pages`} />
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
            <EmptyMessage
              description={`You don't have any favorited artists`}
            />
          )}
        </Grid.Column>
        <Grid.Column>
          {!tags.length && (
            <EmptyMessage description={`You don't have any favorited tags`} />
          )}
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}
