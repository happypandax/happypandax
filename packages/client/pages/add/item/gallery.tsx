import { useCallback, useState } from 'react';
import { Button, Divider } from 'semantic-ui-react';

import t from '../../../client/lang';
import { NewGallery } from '../../../components/create/NewGallery';
import { PageTitle } from '../../../components/misc/index';
import { SourceItem } from '../../../shared/types';
import { FileSegment, Header, ItemBasePage } from './';

export default function Page() {
  const [items, setItems] = useState<SourceItem[]>([]);

  return (
    <ItemBasePage>
      <PageTitle title={t`Add gallery`} />
      <Header active="gallery" />
      <FileSegment
        onCreate={useCallback(
          (i) => {
            setItems([...i, ...items]);
            return true;
          },
          [items]
        )}
      />
      {!!items.length && (
        <Divider horizontal>
          <Button color="green">{t`Add all`}</Button>
        </Divider>
      )}
      {items.map((i, idx) => (
        <NewGallery
          key={`${i.source}-${i.path || i.file.name}`}
          source={i}
          defaultOpen={items.length < 4}
          onClose={() => setItems(items.filter((_, x) => x !== idx))}
        />
      ))}

      {!!items.length && (
        <Divider horizontal>
          <Button color="green">{t`Add all`}</Button>
        </Divider>
      )}
    </ItemBasePage>
  );
}
