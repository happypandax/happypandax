import classNames from 'classnames';
import React, {
  useCallback,
  useContext,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useDebounce } from 'react-use';
import { useRecoilState, useRecoilValue } from 'recoil';
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
import t from '../client/lang';
import { QueryType, useQueryType } from '../client/queries';
import { replaceTextAtPosition } from '../client/search_utils';
import { ItemType } from '../shared/enums';
import {
  SearchItem,
  SearchOptions as SearchOptionsType,
  ServerNamespaceTag,
} from '../shared/types';
import { AppState, SearchState, useInitialRecoilValue } from '../state';
import { itemColor, itemText } from './item/index';
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
          name="heart"
          color="red"
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
                    key={ns + tag}
                    color="red"
                    basic
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
  const recentSearch = useRecoilValue(SearchState.recent(context.stateKey));

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
  itemTypes,
}: {
  itemTypes?: ItemType[];
  onClick?: (ev: any) => void;
  onSelect?: (text: string) => void;
}) {
  const context = useContext(SearchContext);

  const [_searchQuery, setSearchQuery] = useState('');
  const searchQuery = useDeferredValue(_searchQuery);

  const { data } = useQueryType(
    QueryType.SEARCH_LABELS,
    {
      search_query: searchQuery,
      limit: 25,
      item_types: itemTypes ?? [
        ItemType.Artist,
        ItemType.Category,
        ItemType.Circle,
        ItemType.Grouping,
        ItemType.Language,
        ItemType.Parody,
        ItemType.NamespaceTag,
      ],
    },
    {
      enabled: !!searchQuery,
    }
  );

  const searchItems = useCallback((query: string, position: number) => {
    if (query) {
      const t = replaceTextAtPosition(query, '', position, {
        quotation: true,
      });

      const q = query.slice(t.startPosition, t.endPosition);

      setSearchQuery(q.toString());
    }
  }, []);

  useDebounce(
    () => {
      const target = context.ref.current.querySelector('input');
      searchItems(context.query, target.selectionStart);
    },
    300,
    [context.query]
  );

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
          data?.data?.items?.map?.((i) => {
            const color = itemColor(i.__type__);

            let type = itemText(i.__type__) ?? t`Unknown`;
            let basic = false;
            let text = type
              ? `${type.toLowerCase()}:"${i?.name}"`
              : (i?.name as string);

            switch (i.__type__) {
              case ItemType.Collection: {
                type = '';
                text = `"${text}"`;
                break;
              }
              case ItemType.Grouping: {
                basic = true;
                break;
              }
              case ItemType.Language: {
                basic = true;
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
      {(!context.query || !data?.data?.items?.length) && (
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
  const context = useContext(SearchContext);

  const [options, setOptions] = useRecoilState(
    SearchState.options(context.stateKey)
  );

  const [dynamic, setDynamic] = useRecoilState(
    SearchState.dynamic(context.stateKey)
  );

  const [suggest, setSuggest] = useRecoilState(
    SearchState.suggest(context.stateKey)
  );

  const { data } = useQueryType(QueryType.CONFIG, {
    cfg: {
      'search.case_sensitive': false,
      'search.regex': false,
      'search.match_exact': false,
      'search.match_all_terms': false,
      'search.children': false,
    },
  });

  type Config = Record<'search', SearchOptionsType>;

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
            checked={
              options.case_sensitive ??
              (data?.data as Config)?.search?.case_sensitive
            }
            onChange={useCallback(
              (e, d) =>
                setOptions({
                  ...options,
                  case_sensitive: d.checked,
                }),
              [options]
            )}
            label={t`Case sensitive`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.regex"
            checked={options.regex ?? (data?.data as Config)?.search?.regex}
            onChange={useCallback(
              (e, d) =>
                setOptions({
                  ...options,
                  regex: d.checked,
                }),
              [options]
            )}
            label={t`Regex`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.exact"
            checked={
              options.match_exact ?? (data?.data as Config)?.search?.match_exact
            }
            onChange={useCallback(
              (e, d) =>
                setOptions({
                  ...options,
                  match_exact: d.checked,
                }),
              [options]
            )}
            label={t`Match terms exactly`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.all"
            checked={
              options.match_all_terms ??
              (data?.data as Config)?.search?.match_all_terms
            }
            onChange={useCallback(
              (e, d) =>
                setOptions({
                  ...options,
                  match_all_terms: d.checked,
                }),
              [options]
            )}
            label={t`Match all terms`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.children"
            checked={
              options.children ?? (data?.data as Config)?.search?.children
            }
            onChange={useCallback(
              (e, d) =>
                setOptions({
                  ...options,
                  children: d.checked,
                }),
              [options]
            )}
            label={t`Match on children`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.suggest"
            checked={suggest}
            onChange={useCallback((e, d) => setSuggest(d.checked), [])}
            label={t`Show suggestions`}
          />
        </List.Item>
        <List.Item>
          <Checkbox
            toggle
            name="search.dynamic"
            checked={dynamic}
            onChange={useCallback((e, d) => setDynamic(d.checked), [])}
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
  debounce = 500,
  defaultValue,
  onSearch,
  showSuggestion,
  dynamic: initialDynamic,
  itemTypes,
  stateKey,
  showOptions,
  onClear: cOnClear,
  className,
}: {
  fluid?: boolean;
  transparent?: boolean;
  debounce?: number;
  defaultValue?: string;
  itemTypes?: ItemType[];
  stateKey?: string;
  dynamic?: boolean;
  showSuggestion?: boolean;
  showOptions?: boolean;
  placeholder?: string;
  onSearch?: (query: string, options: object) => void;
  onClear?: () => void;
  size?: React.ComponentProps<typeof Search>['size'];
  className?: string;
}) {
  const ref = useRef<HTMLElement>();
  const refTimeoutId = useRef<NodeJS.Timeout>();
  const [query, setQuery] = useState(defaultValue);
  const deferredQuery = useDeferredValue(query);
  const [resultsVisible, setResultsVisible] = useState(false);
  const [focused, setFocused] = useState(false);
  const options = useRecoilValue(SearchState.options(stateKey));
  const dynamic = useInitialRecoilValue(
    SearchState.dynamic(stateKey),
    initialDynamic
  );
  const suggest = useInitialRecoilValue(
    SearchState.suggest(stateKey),
    showSuggestion
  );

  const onSubmit = useCallback(
    (ev?) => {
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

  const onSearchResultClick = useCallback((ev) => {
    const target = ref.current.querySelector('input');
    target.focus();
  }, []);

  useDebounce(
    () => {
      if (dynamic) {
        onSubmit();
      }
    },
    debounce,
    [dynamic, onSubmit]
  );

  useEffect(() => {
    if (query) {
      onSubmit();
    }
  }, [options]);

  const onSearchResultSelect = useCallback(
    (text) => {
      const target = ref.current.querySelector('input');
      target.focus();
      const t = replaceTextAtPosition(query, text, target.selectionStart, {
        quotation: true,
      });
      target.value = t.text;
      target.focus();
      //   document.getSelection().collapse(ref.current, t.newPosition)
      target.setSelectionRange(t.newEndPosition, t.newEndPosition);
      setQuery(t.text);
    },
    [query]
  );

  const optionsEl = useMemo(
    () => (
      <>
        <div>
          <SearchOptions size={size} />
          {!!deferredQuery && <Icon name="remove" link onClick={onClear} />}
        </div>
      </>
    ),
    [deferredQuery, onClear]
  );

  return (
    <SearchContext.Provider
      value={useMemo(() => ({ query: deferredQuery, stateKey, ref }), [
        deferredQuery,
      ])}>
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
              placeholder={placeholder ?? t`Search`}
              label={showOptions ? optionsEl : undefined}
              icon={useMemo(
                () => ({ name: 'search', link: true, onClick: onSubmit }),
                []
              )}
              tabIndex={0}
              value={query}
              onChange={useCallback((ev, d) => {
                ev.preventDefault();
                setFocused(true);
                setQuery(d.value);
              }, [])}
            />
          </Ref>
          {suggest && (
            <div
              className={classNames('results transition', {
                visible: resultsVisible,
              })}>
              <SearchResults
                itemTypes={itemTypes}
                onClick={onSearchResultClick}
                onSelect={onSearchResultSelect}
              />
            </div>
          )}
        </div>
      </form>
    </SearchContext.Provider>
  );
}
