import classNames from 'classnames';
import _ from 'lodash';
import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useRecoilValue } from 'recoil';
import {
  Button,
  Checkbox,
  Divider,
  Header,
  Icon,
  Input,
  Label,
  List,
  Popup,
  Ref,
  Search,
  Segment,
} from 'semantic-ui-react';
import SwiperCore, { Mousewheel } from 'swiper/core';
import { Swiper, SwiperSlide } from 'swiper/react';

import { SearchContext } from '../client/context';
import { Query, QueryType, useQueryType } from '../client/queries';
import { replaceTextAtPosition } from '../client/search_utils';
import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { SearchItem, ServerNamespaceTag } from '../misc/types';
import { AppState, MiscState } from '../state';
import styles from './Search.module.css';

SwiperCore.use([Mousewheel]);

function TagsLine({ onClick }: { onClick: (text: string) => void }) {
  const properties = useRecoilValue(AppState.properties);

  const { data } = useQueryType(QueryType.ITEMS, {
    item_type: ItemType.NamespaceTag,
    limit: 50,
    fields: ['tag.name', 'namespace.name'],
    metatags: {
      favorite: true,
    },
  });

  if (!data?.data?.count) {
    return null;
  }

  return (
    <>
      <Segment
        basic
        className={classNames(
          styles.searchline,
          'small-padding-segment no-margins'
        )}>
        <Icon
          name="star"
          color="yellow"
          bordered
          size="small"
          circular
          className={styles.searchline_icon}
        />
        <Swiper
          resistance={true}
          slidesPerView={'auto'}
          freeMode
          mousewheel
          spaceBetween={0}>
          <SwiperSlide className={styles.tagsline_swipeslide}>
            <Label.Group className={classNames(styles.tagsline_labels)}>
              {data?.data?.items?.map?.((t: ServerNamespaceTag) => {
                const ns =
                  t?.namespace?.name === properties.special_namespace
                    ? t?.tag?.name
                    : t?.namespace?.name;
                const tag =
                  t?.namespace?.name !== properties.special_namespace
                    ? t?.tag?.name
                    : undefined;

                return (
                  <Label
                    as="a"
                    className="no-bottom-margin"
                    onClick={(ev) => {
                      const n = tag ? `"${ns}":"${tag}"` : `"${ns}"`;
                      ev.preventDefault();
                      onClick?.(n);
                    }}>
                    {ns}
                    {!!tag && <Label.Detail>{tag}</Label.Detail>}
                  </Label>
                );
              })}
            </Label.Group>
          </SwiperSlide>
        </Swiper>
      </Segment>
      <Divider className="no-margins" />
    </>
  );
}

function RecentSearch({ onClick }: { onClick: (text: string) => void }) {
  const context = useContext(SearchContext);
  const recentSearch = useRecoilValue(MiscState.recentSearch(context.stateKey));

  const onItemClick = useCallback((ev, d) => {
    ev.preventDefault();
    onClick?.(d.content);
  }, []);

  if (!recentSearch.length) {
    return null;
  }

  return (
    <>
      <Segment
        basic
        className={classNames(
          styles.searchline,
          'small-padding-segment no-margins'
        )}>
        <Icon
          name="history"
          size="small"
          bordered
          circular
          className={styles.searchline_icon}
        />
        <List
          selection
          onItemClick={onItemClick}
          className={classNames(styles.searchline_content, 'no-margins')}
          items={recentSearch}
        />
      </Segment>
      <Divider className="no-margins" />
    </>
  );
}

function SearchResult({
  text,
  className,
  type,
  children,
  basic,
  size,
  onClick,
  color,
  ...props
}: Omit<React.ComponentProps<typeof Label>, 'onClick'> & {
  text: string;
  onClick: (text: string) => void;
}) {
  return (
    <List.Item
      onClick={useCallback(
        (ev) => {
          ev.preventDefault();
          onClick?.(text);
        },
        [text, onClick]
      )}
      className={classNames('no-left-padding no-left-margin', className)}>
      <Label
        className={classNames('no-left-margin')}
        basic={basic}
        size="small"
        color={color}
        {...props}>
        {type}
      </Label>
      <span className="small-padding-segment">{children}</span>
    </List.Item>
  );
}

function ArtistSearchResult({
  item,
  onClick,
}: {
  item: SearchItem;
  onClick: (text: string) => void;
}) {
  return (
    <SearchResult
      type={t`Artist`}
      color="blue"
      onClick={onClick}
      text={`artist:"${item?.names?.[0]?.name}"`}>
      {item?.names?.[0]?.name}
    </SearchResult>
  );
}

function TagResult({
  item,
  onClick,
}: {
  item: SearchItem;
  onClick: (text: string) => void;
}) {
  const properties = useRecoilValue(AppState.properties);
  const text =
    properties.special_namespace === item.namespace
      ? `${item.tag}`
      : `${item.namespace}:${item.tag}`;

  return (
    <SearchResult type={t`Tag`} onClick={onClick} text={text}>
      {text}
    </SearchResult>
  );
}

function SearchResults({
  onSelect,
  onClick,
}: {
  onClick?: (ev: any) => void;
  onSelect?: (text: string) => void;
}) {
  const context = useContext(SearchContext);

  const [data, setData] = useState<SearchItem[]>([]);

  const searchItems = useCallback(
    _.debounce(
      (query: string, position: number) => {
        if (query) {
          const t = replaceTextAtPosition(query, '', position, {
            quotation: true,
          });

          const q = query.slice(t.startPosition, t.endPosition);

          Query.get(QueryType.SEARCH_ITEMS, {
            item_types: [
              ItemType.Artist,
              ItemType.Category,
              ItemType.Circle,
              ItemType.Grouping,
              ItemType.Language,
              ItemType.Parody,
              ItemType.NamespaceTag,
            ],
            search_query: q,
            limit: 25,
          }).then((r) => {
            setData(r.data.items);
          });
        }
      },
      200,
      { maxWait: 1000 }
    ),
    []
  );

  useEffect(() => {
    const target = context.ref.current.querySelector('input');
    searchItems(context.query, target.selectionStart);
  }, [context.query]);

  return (
    <Segment
      onClick={onClick}
      onContextMenu={onClick}
      basic
      className={classNames('no-margins no-padding-segment')}>
      <TagsLine onClick={onSelect} />
      <RecentSearch onClick={onSelect} />
      <List
        relaxed
        divided
        verticalAlign="middle"
        selection
        className="no-margins small-padding-segment max-200-h overflow-y-auto">
        {!!context.query &&
          data?.map?.((i) => {
            let basic = false;
            let type = t`Unknown`;
            let text = i?.name as string;
            let color: React.ComponentProps<typeof Label>['color'];
            switch (i.__type__) {
              case ItemType.Category: {
                type = t`Category`;
                text = `category:"${text}"`;
                color = 'black';
                break;
              }
              case ItemType.Circle: {
                type = t`Circle`;
                text = `circle:"${text}"`;
                color = 'teal';
                break;
              }
              case ItemType.Grouping: {
                type = t`Series`;
                basic = true;
                text = `series:"${text}"`;
                color = 'black';
                break;
              }
              case ItemType.Language: {
                type = t`Language`;
                color = 'blue';
                text = `language:"${text}"`;
                basic = true;
                break;
              }
              case ItemType.Parody: {
                type = t`Parody`;
                text = `parody:"${text}"`;
                color = 'violet';
                break;
              }
            }

            switch (i.__type__) {
              case ItemType.Artist:
                return (
                  <ArtistSearchResult
                    onClick={onSelect}
                    key={i.__type__ + i.id}
                    item={i}
                  />
                );
              case ItemType.NamespaceTag:
                return (
                  <TagResult
                    onClick={onSelect}
                    key={i.__type__ + i.id}
                    item={i}
                  />
                );
              default:
                return (
                  <SearchResult
                    key={i.__type__ + i.id}
                    type={type}
                    onClick={onSelect}
                    basic={basic}
                    text={text}
                    color={color}>
                    {i?.name}
                  </SearchResult>
                );
            }
          })}
      </List>
      {(!context.query || !data?.length) && (
        <Header
          textAlign="center"
          className="sub-text no-margins"
          content="• • •"
        />
      )}
      <Divider hidden className="very thin" />
    </Segment>
  );
}

function SearchOptions({
  size,
}: {
  size?: React.ComponentProps<typeof Button>['size'];
}) {
  return (
    <Popup
      trigger={
        <Button
          basic
          type="button"
          size={size}
          icon={
            <Icon.Group>
              <Icon name="options" />
              <Icon name="search" corner />
            </Icon.Group>
          }
        />
      }
      hoverable
      on="click"
      hideOnScroll>
      <List>
        <List.Item>
          <Checkbox
            toggle
            name="search.case"
            defaultChecked
            label={t`Case sensitive`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.regex"
            defaultChecked
            label={t`Regex`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.exact"
            defaultChecked
            label={t`Match terms exactly`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.all"
            defaultChecked
            label={t`Match all terms`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.suggest"
            defaultChecked
            label={t`Show suggestions`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.dynamic"
            defaultChecked
            label={t`Dynamic`}
          />
        </List.Item>
      </List>
    </Popup>
  );
}

export function ItemSearch({
  size,
  fluid,
  transparent = true,
  placeholder,
  defaultValue,
  onSearch,
  stateKey,
  showOptions,
  onClear: cOnClear,
  className,
}: {
  fluid?: boolean;
  transparent?: boolean;
  defaultValue?: string;
  stateKey?: string;
  showOptions?: boolean;
  placeholder?: string;
  onSearch?: (query: string, options: object) => void;
  onClear?: () => void;
  size?: React.ComponentProps<typeof Search>['size'];
  className?: string;
}) {
  const ref = useRef<HTMLElement>();
  const refTimeoutId = useRef<NodeJS.Timeout>();
  const [query, setQuery] = useState('');
  const [resultsVisible, setResultsVisible] = useState(false);
  const [focused, setFocused] = useState(false);

  const onSubmit = useCallback(
    (ev) => {
      ev?.preventDefault?.();
      onSearch?.(query, {});
      setFocused(false);
    },
    [query]
  );

  const onClear = useCallback(() => {
    setQuery('');
    cOnClear?.();
  }, [cOnClear]);

  useEffect(() => {
    setResultsVisible(focused);
  }, [focused]);

  const onFocus = useCallback(() => {
    clearTimeout(refTimeoutId.current);
    setFocused(true);
  }, []);

  const onBlur = useCallback(() => {
    refTimeoutId.current = setTimeout(() => {
      setFocused(false);
    }, 250);
  }, []);

  return (
    <SearchContext.Provider
      value={useMemo(() => ({ query, stateKey, ref }), [query])}>
      <form
        onSubmit={onSubmit}
        className={classNames({ fullwidth: fluid }, className)}>
        <div className={classNames('ui search', size, { fluid })}>
          <Ref innerRef={ref}>
            <Input
              fluid={fluid}
              onFocus={onFocus}
              onBlur={onBlur}
              className={classNames({ secondary: transparent })}
              placeholder={placeholder}
              label={
                showOptions
                  ? useMemo(
                      () => (
                        <>
                          <div>
                            <SearchOptions size={size} />
                            {!!query && (
                              <Icon name="remove" link onClick={onClear} />
                            )}
                          </div>
                        </>
                      ),
                      [query, onClear]
                    )
                  : undefined
              }
              icon={useMemo(
                () => ({ name: 'search', link: true, onClick: onSubmit }),
                []
              )}
              tabIndex={0}
              defaultValue={defaultValue}
              value={query}
              onChange={useCallback((ev, d) => {
                ev.preventDefault();
                setFocused(true);
                setQuery(d.value);
              }, [])}
            />
          </Ref>
          <div
            className={classNames('results transition', {
              visible: resultsVisible,
            })}>
            <SearchResults
              onClick={useCallback((ev) => {
                const target = ref.current.querySelector('input');
                target.focus();
              }, [])}
              onSelect={useCallback(
                (text) => {
                  const target = ref.current.querySelector('input');
                  target.focus();
                  const t = replaceTextAtPosition(
                    query,
                    text,
                    target.selectionStart,
                    {
                      quotation: true,
                    }
                  );
                  console.log(t.text);
                  target.value = t.text;
                  target.focus();
                  //   document.getSelection().collapse(ref.current, t.newPosition)
                  target.setSelectionRange(t.newEndPosition, t.newEndPosition);
                  setQuery(t.text);
                },
                [query]
              )}
            />
          </div>
        </div>
      </form>
    </SearchContext.Provider>
  );
}
