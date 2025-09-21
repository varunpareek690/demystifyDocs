import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProfileBadge } from './profile-badge';

describe('ProfileBadge', () => {
  let component: ProfileBadge;
  let fixture: ComponentFixture<ProfileBadge>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfileBadge]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProfileBadge);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
