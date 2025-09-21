import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FeaturePlaceholder } from './feature-placeholder';

describe('FeaturePlaceholder', () => {
  let component: FeaturePlaceholder;
  let fixture: ComponentFixture<FeaturePlaceholder>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FeaturePlaceholder]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FeaturePlaceholder);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
