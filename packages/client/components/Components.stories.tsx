import { Label } from 'semantic-ui-react';

import GalleryCard from './item/Gallery';
import { ViewButtons as ViewButtonsC } from './layout/GalleryLayout';
import { EmptySegment, LabelAccordion as LabelAccordionC } from './misc';
import { Slider as SliderC } from './Slider';

export default {
  title: 'Components/Misc',
};

export const ViewButtons = () => <ViewButtonsC />;

export const Slider = () => (
  <div>
    <SliderC />
    <SliderC label="Label">
      <GalleryCard size="small" data={{ id: 1, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 2, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 3, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 4, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 5, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 6, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 7, title: 'yes', artist: 'no' }} />
      <GalleryCard size="small" data={{ id: 8, title: 'yes', artist: 'no' }} />
    </SliderC>
  </div>
);

export const LabelAccordion = () => (
  <div>
    <LabelAccordionC label="Title">
      <SliderC>
        <GalleryCard
          size="small"
          data={{ id: 1, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 2, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 3, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 4, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 5, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 6, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 7, title: 'yes', artist: 'no' }}
        />
        <GalleryCard
          size="small"
          data={{ id: 8, title: 'yes', artist: 'no' }}
        />
      </SliderC>
    </LabelAccordionC>
    <LabelAccordionC Label="Empty" detail="Detail">
      <EmptySegment />
    </LabelAccordionC>
  </div>
);
