import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';

import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { CheckboxModule } from 'primeng/checkbox';
import { BadgeModule } from 'primeng/badge';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressBarModule } from 'primeng/progressbar';
import { InputNumberModule } from 'primeng/inputnumber';
import { MessageService } from 'primeng/api';

import { ApiEventService } from '../../services/api-event.service';
import { ApiDishService } from '../../services/api-dish.service';
import { ApiToolService } from '../../services/api-tool.service';
import { ApiMenuService } from '../../services/api-menu.service';
import { ApiEvent, EventDishCreate, ApiEventDish, DishServingSet, ApiDish, ApiTool } from '../../core/models/api.models';
import { MenuTemplate, MenuSubMeal, MenuCategory, DishMenuMapping, CategoryDishesResponse } from '../../models/menu.model';

// ============================================
// Wizard Step — שלב בודד ב-wizard
// ============================================
export interface WizardStep {
  index: number;
  title: string;                     // כותרת מלאה: "ליל שבת - סלטים"
  subMealId: number | null;
  subMealName: string | null;
  categoryId: number;
  categoryName: string;
  categoryNameHebrew: string;
  quota: number | null;              // null = ללא הגבלה
  quotaDescription: string | null;
  isRequired: boolean;
  isTrayCategory: boolean;
  trayPrice: number | null;
  // Lazy-loaded data
  standardDishes: DishMenuMapping[];
  upgradeDishes: DishMenuMapping[];
  loaded: boolean;
  loading: boolean;
  // Live selection state
  selectedDishIds: Set<number>;
}

@Component({
  selector: 'app-event-dish-wizard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    TagModule,
    ToastModule,
    CheckboxModule,
    BadgeModule,
    TooltipModule,
    ProgressBarModule,
    InputNumberModule
  ],
  providers: [MessageService],
  templateUrl: './event-dish-wizard.component.html',
  styleUrls: ['./event-dish-wizard.component.scss']
})
export class EventDishWizardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Event data
  eventId!: number;
  event: ApiEvent | null = null;
  menuTemplate: MenuTemplate | null = null;

  // Wizard state
  steps: WizardStep[] = [];
  activeStepIndex = 0;
  initialLoading = true;
  isTrayMenu = false;

  // Track saving state per dish
  savingDishIds = new Set<number>();
  giftDishIds = new Set<number>();
  servingSets = new Map<number, DishServingSet[]>();
  selectedServingSets: Record<string, number> = {};

  extrasOpen = false;
  private extraSearchRequest = 0;
  extraSearch = '';
  extraResults: ApiDish[] = [];
  extraTools: ApiTool[] = [];
  manualTools: Array<{tool_id?: number | null; name?: string; quantity: number; is_reusable: boolean; notes?: string}> = [];
  extrasLoaded = false;
  extrasLoading = false;
  manualSaving = false;
  newToolId: number | null = null;
  newToolQuantity = 1;
  // Q045 (2026-11-23): approved events stay editable with a warning; completed/cancelled are closed.
  get editable(): boolean { return this.event?.status === 'טיוטה' || this.event?.status === 'מאושר'; }
  get isApproved(): boolean { return this.event?.status === 'מאושר'; }
  get freeDishes(): ApiEventDish[] { return (this.event?.dishes || []).filter(d => !d.category_id); }

  // Summary mode
  showSummary = false;

  // Group labels for sub-meal transitions
  get currentStep(): WizardStep | null {
    return this.steps[this.activeStepIndex] ?? null;
  }

  get isFirstStep(): boolean {
    return this.activeStepIndex === 0;
  }

  get isLastStep(): boolean {
    return this.activeStepIndex === this.steps.length - 1;
  }

  get totalSelected(): number {
    return this.freeDishes.length + this.steps.reduce((sum, s) => sum + s.selectedDishIds.size, 0);
  }

  /** Count only standard dishes (exclude upgrades) for quota checking */
  getStandardDishCount(step: WizardStep): number {
    if (!step.loaded) return Array.from(step.selectedDishIds).filter(id => !this.giftDishIds.has(id)).length;
    const standardDishIds = new Set(step.standardDishes.map(d => d.dish_id));
    return Array.from(step.selectedDishIds).filter(id => standardDishIds.has(id) && !this.giftDishIds.has(id)).length;
  }

  getGiftDishCount(step: WizardStep): number {
    return Array.from(step.selectedDishIds).filter(id => this.giftDishIds.has(id)).length;
  }

  /** Check if current step's sub-meal differs from previous step */
  get isNewSubMealGroup(): boolean {
    if (this.activeStepIndex === 0) return true;
    const prev = this.steps[this.activeStepIndex - 1];
    const curr = this.steps[this.activeStepIndex];
    return prev?.subMealId !== curr?.subMealId;
  }

  /** Get distinct sub-meal groups for summary */
  get subMealGroups(): { name: string | null; subMealId: number | null; steps: WizardStep[] }[] {
    const groups: { name: string | null; subMealId: number | null; steps: WizardStep[] }[] = [];
    for (const step of this.steps) {
      const existing = groups.find(g => g.subMealId === step.subMealId);
      if (existing) {
        existing.steps.push(step);
      } else {
        groups.push({ name: step.subMealName, subMealId: step.subMealId, steps: [step] });
      }
    }
    return groups;
  }

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private eventService: ApiEventService,
    private dishService: ApiDishService,
    private menuService: ApiMenuService,
    private toolService: ApiToolService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
      this.eventId = +params['eventId'];
      this.loadEventAndTemplate();
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ========================================
  // Initialization
  // ========================================

  private loadEventAndTemplate(): void {
    this.initialLoading = true;
    this.eventService.getEvent(this.eventId).pipe(takeUntil(this.destroy$)).subscribe({
      next: (event) => {
        this.event = event;
        this.eventService.getDishServingSelections(this.eventId).pipe(takeUntil(this.destroy$)).subscribe({
          next: selections => {
            this.selectedServingSets = {};
            selections.forEach(row => this.selectedServingSets[`${row.dish_id}:${row.set_type}`] = row.set_id);
            this.loadMenuTemplate(event.menu_type);
          },
          error: () => { this.initialLoading = false; this.messageService.add({severity: 'error', summary: 'לא ניתן לטעון את בחירות ההגשה. יש לרענן ולנסות שוב'}); }
        });
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'לא ניתן לטעון את האירוע' });
        this.initialLoading = false;
      }
    });
  }

  private loadMenuTemplate(menuType: string): void {
    this.menuService.getMenuByType(menuType).pipe(takeUntil(this.destroy$)).subscribe({
      next: (template) => {
        this.menuTemplate = template;
        this.isTrayMenu = template.is_tray_menu;
        this.buildSteps(template);
        this.initialLoading = false;
        // Load first step's dishes
        if (this.steps.length > 0) {
          this.loadStepDishes(this.steps[0]);
        }
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'לא נמצא תבנית תפריט מתאימה' });
        this.initialLoading = false;
      }
    });
  }

  private buildSteps(template: MenuTemplate): void {
    this.steps = [];
    let index = 0;

    if (template.sub_meals && template.sub_meals.length > 0) {
      // Sub-meal menus (e.g., שבת) — iterate sub-meals then categories
      const sortedSubMeals = [...template.sub_meals].sort((a, b) => a.display_order - b.display_order);
      for (const subMeal of sortedSubMeals) {
        const sortedCats = [...(subMeal.categories || [])].sort((a, b) => a.display_order - b.display_order);
        for (const cat of sortedCats) {
          this.steps.push(this.createStep(index++, cat, subMeal));
        }
      }
    }

    if (template.categories && template.categories.length > 0) {
      // Direct categories (non-sub-meal menus)
      const sortedCats = [...template.categories].sort((a, b) => a.display_order - b.display_order);
      for (const cat of sortedCats) {
        this.steps.push(this.createStep(index++, cat, null));
      }
    }

    // Pre-populate selections from existing event dishes
    this.populateExistingSelections();
  }

  private createStep(index: number, cat: MenuCategory, subMeal: MenuSubMeal | null): WizardStep {
    const subMealPrefix = subMeal ? `${subMeal.name} - ` : '';
    return {
      index,
      title: `${subMealPrefix}${cat.name_hebrew}`,
      subMealId: subMeal?.id ?? null,
      subMealName: subMeal?.name ?? null,
      categoryId: cat.id!,
      categoryName: cat.name,
      categoryNameHebrew: cat.name_hebrew,
      quota: cat.quota ?? null,
      quotaDescription: cat.quota_description ?? null,
      isRequired: cat.is_required,
      isTrayCategory: this.isTrayMenu,
      trayPrice: cat.tray_price ?? null,
      standardDishes: [],
      upgradeDishes: [],
      loaded: false,
      loading: false,
      selectedDishIds: new Set<number>()
    };
  }

  private populateExistingSelections(): void {
    if (!this.event?.dishes) return;
    for (const dish of this.event.dishes) {
      const step = this.steps.find(s =>
        s.categoryId === dish.category_id &&
        s.subMealId === (dish.sub_meal_id ?? null)
      );
      if (step) {
        step.selectedDishIds.add(dish.dish_id);
        if (dish.is_gift) this.giftDishIds.add(dish.dish_id);
      }
    }
  }

  // ========================================
  // Dish Loading (lazy per step)
  // ========================================

  private loadStepDishes(step: WizardStep): void {
    if (step.loaded || step.loading) return;
    step.loading = true;

    this.menuService.getCategoryDishes(step.categoryId).pipe(takeUntil(this.destroy$)).subscribe({
      next: (response: CategoryDishesResponse) => {
        step.standardDishes = response.standard_dishes || [];
        step.upgradeDishes = response.upgrade_dishes || [];
        step.loaded = true;
        step.loading = false;
        this.loadServingSets([...step.standardDishes, ...step.upgradeDishes]);
      },
      error: () => {
        step.loading = false;
        this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: `לא ניתן לטעון מנות עבור ${step.categoryNameHebrew}` });
      }
    });
  }

  private loadServingSets(dishes: Array<{dish_id: number}>): void {
    const missing = dishes.filter(dish => !this.servingSets.has(dish.dish_id));
    if (!missing.length) return;
    forkJoin(missing.map(dish => this.dishService.getServingSets(dish.dish_id)))
      .pipe(takeUntil(this.destroy$))
      .subscribe(results => results.forEach((sets, index) => {
        const dishId = missing[index].dish_id;
        this.servingSets.set(dishId, sets);
        for (const type of ['serving', 'packaging'] as const) {
          const candidates = this.getServingSets(dishId, type);
          const defaultSet = candidates.find(set => set.is_default) || (candidates.length === 1 ? candidates[0] : undefined);
          if (defaultSet?.id && !this.selectedServingSets[`${dishId}:${type}`]) this.selectedServingSets[`${dishId}:${type}`] = defaultSet.id;
        }
      }));
  }

  getServingSets(dishId: number, type: 'serving' | 'packaging'): DishServingSet[] {
    const sets = (this.servingSets.get(dishId) || []).filter(set => set.set_type === type);
    if (type !== 'serving' || !sets.some(set => set.serving_mode)) return sets;
    const kind = this.event?.is_real_dishes ? 'real' : 'disposable';
    return sets.filter(set => !!set.serving_mode && set.dishware_type === kind);
  }

  saveServingSetSelection(dishId: number, type: 'serving' | 'packaging', setId: number): void {
    this.selectedServingSets[`${dishId}:${type}`] = Number(setId);
    const selections = Object.entries(this.selectedServingSets).map(([key, selectedSetId]) => {
      const [selectedDishId, setType] = key.split(':');
      return { dish_id: Number(selectedDishId), set_id: selectedSetId, set_type: setType };
    });
    this.eventService.updateDishServingSelections(this.eventId, selections)
      .pipe(takeUntil(this.destroy$)).subscribe({error: () => this.messageService.add({severity: 'error', summary: 'בחירת ההגשה לא נשמרה. יש לרענן ולנסות שוב'})});
  }

  servingMode(dishId: number): 'personal' | 'central' | null {
    return this.servingEventDish(dishId)?.serving_mode ?? null;
  }

  private servingEventDish(dishId: number): ApiEventDish | undefined {
    const step = this.currentStep;
    return this.event?.dishes?.find(d => d.dish_id === dishId && (!step ||
      (d.category_id === step.categoryId && (d.sub_meal_id ?? null) === step.subMealId)));
  }

  setServingMode(dishId: number, mode: 'personal' | 'central' | null, eventDishId?: number): void {
    if (!this.editable || this.savingDishIds.has(dishId)) return;
    this.savingDishIds.add(dishId);
    this.eventService.updateEventDish(this.eventId, dishId, {serving_mode: mode}, eventDishId ?? this.servingEventDish(dishId)?.id)
      .pipe(takeUntil(this.destroy$)).subscribe({
        next: event => { this.event = event; this.savingDishIds.delete(dishId); },
        error: () => { this.savingDishIds.delete(dishId); this.messageService.add({severity: 'error', summary: 'צורת ההגשה לא נשמרה'}); }
      });
  }

  openExtras(): void {
    this.extrasOpen = !this.extrasOpen;
    if (!this.extrasOpen || this.extrasLoaded || this.extrasLoading) return;
    this.extrasLoading = true;
    forkJoin({tools: this.toolService.getAllTools(), rows: this.eventService.getManualTools(this.eventId)})
      .pipe(takeUntil(this.destroy$)).subscribe({next: data => {
        this.extraTools = data.tools; this.manualTools = data.rows; this.extrasLoaded = true; this.extrasLoading = false;
        this.searchExtraDishes();
      }, error: () => { this.extrasLoading = false; this.messageService.add({severity: 'error', summary: 'לא ניתן לטעון תוספות. סגרו ופתחו שוב כדי לנסות מחדש'}); }});
  }

  searchExtraDishes(): void {
    const request = ++this.extraSearchRequest;
    this.extraResults = [];
    this.dishService.getDishes({search: this.extraSearch, is_active: true, limit: 200})
      .pipe(takeUntil(this.destroy$)).subscribe({next: result => { if (request === this.extraSearchRequest) this.extraResults = result.items; },
        error: () => this.messageService.add({severity: 'error', summary: 'חיפוש המנות נכשל'})});
  }

  alreadySelected(dishId: number): boolean { return !!this.event?.dishes?.some(d => d.dish_id === dishId); }

  addFreeDish(dish: ApiDish): void {
    if (!this.editable || this.alreadySelected(dish.id) || this.savingDishIds.has(dish.id)) return;
    this.savingDishIds.add(dish.id);
    // Q007: an extra/upgrade dish is sized like a regular dish (guests ÷ serving size).
    const quantity = Math.ceil((this.event?.guest_count || 1) / (dish.serving_size || 1));
    this.eventService.addDishToEvent(this.eventId, {dish_id: dish.id, quantity, is_upgrade: true,
      extra_charge: dish.client_price || 0}).pipe(takeUntil(this.destroy$)).subscribe({next: event => {
        this.event = event; this.savingDishIds.delete(dish.id);
      }, error: () => {this.savingDishIds.delete(dish.id); this.messageService.add({severity: 'error', summary: 'המנה לא נוספה'});}});
  }

  removeFreeDish(dishId: number): void {
    if (!this.editable || this.savingDishIds.has(dishId)) return;
    this.savingDishIds.add(dishId);
    this.eventService.removeDishFromEvent(this.eventId, dishId).pipe(takeUntil(this.destroy$)).subscribe({next: () => {
      if (this.event) this.event.dishes = this.event.dishes?.filter(d => d.dish_id !== dishId);
      this.giftDishIds.delete(dishId); this.savingDishIds.delete(dishId);
    }, error: () => {this.savingDishIds.delete(dishId); this.messageService.add({severity: 'error', summary: 'ההסרה נכשלה'});}});
  }

  setFreeGift(dish: ApiEventDish, value: boolean): void {
    if (!this.editable || this.savingDishIds.has(dish.dish_id)) return;
    this.savingDishIds.add(dish.dish_id);
    this.eventService.updateEventDish(this.eventId, dish.dish_id, {is_gift: value}).pipe(takeUntil(this.destroy$)).subscribe({next: event => {
      this.event = event; this.savingDishIds.delete(dish.dish_id);
    }, error: () => {this.savingDishIds.delete(dish.dish_id); this.messageService.add({severity: 'error', summary: 'סימון המתנה לא נשמר'});}});
  }

  addFreeTool(): void {
    if (!this.editable || !this.extrasLoaded || this.manualSaving) return;
    const tool = this.extraTools.find(t => t.id === Number(this.newToolId));
    if (!tool || !Number.isInteger(this.newToolQuantity) || this.newToolQuantity < 1) return;
    const rows = this.manualTools.map(r => ({...r}));
    const existing = rows.find(r => r.tool_id === tool.id);
    if (existing) existing.quantity += this.newToolQuantity;
    else rows.push({tool_id: tool.id, name: tool.name, quantity: this.newToolQuantity, is_reusable: tool.sub_category === 'אמיתי'});
    this.persistManualTools(rows);
  }

  removeFreeTool(index: number): void {
    if (this.editable && !this.manualSaving) this.persistManualTools(this.manualTools.filter((_, i) => i !== index));
  }

  private persistManualTools(rows: typeof this.manualTools): void {
    this.manualSaving = true;
    this.eventService.updateManualTools(this.eventId, rows).pipe(takeUntil(this.destroy$)).subscribe({next: () => {
      this.manualTools = rows; this.manualSaving = false;
      this.messageService.add({severity: 'success', summary: 'הכלים נשמרו באירוע'});
    }, error: () => {this.manualSaving = false; this.messageService.add({severity: 'error', summary: 'הכלים לא נשמרו'});}});
  }

  // ========================================
  // Navigation
  // ========================================

  goToStep(index: number): void {
    if (index < 0 || index >= this.steps.length) return;
    this.showSummary = false;
    this.activeStepIndex = index;
    const step = this.steps[index];
    if (!step.loaded) {
      this.loadStepDishes(step);
    }
  }

  nextStep(): void {
    if (this.isLastStep) {
      this.showSummary = true;
    } else {
      this.goToStep(this.activeStepIndex + 1);
    }
  }

  prevStep(): void {
    if (this.showSummary) {
      this.showSummary = false;
      return;
    }
    this.goToStep(this.activeStepIndex - 1);
  }

  goToSummary(): void {
    this.showSummary = true;
  }

  // ========================================
  // Dish Selection — immediate save
  // ========================================

  isDishSelected(step: WizardStep, dishId: number): boolean {
    return step.selectedDishIds.has(dishId);
  }

  isQuotaReached(step: WizardStep): boolean {
    if (!step.quota) return false;
    return this.getStandardDishCount(step) >= step.quota;
  }

  isDishDisabled(step: WizardStep, dishId: number): boolean {
    // Only disable if saving
    return this.savingDishIds.has(dishId);
  }

  isGiftDish(dishId: number): boolean {
    return this.giftDishIds.has(dishId);
  }

  toggleGift(dishId: number, event: MouseEvent): void {
    event.stopPropagation();
    if (this.savingDishIds.has(dishId)) return;

    const isGift = !this.giftDishIds.has(dishId);
    this.savingDishIds.add(dishId);
    this.eventService.updateEventDish(this.eventId, dishId, { is_gift: isGift })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          isGift ? this.giftDishIds.add(dishId) : this.giftDishIds.delete(dishId);
          this.savingDishIds.delete(dishId);
          this.messageService.add({
            severity: 'success',
            summary: isGift ? 'המנה סומנה כמתנה' : 'סימון המתנה הוסר',
            detail: isGift ? 'המנה לא תחויב במחיר האירוע' : 'המנה תחושב שוב לפי התמחור שלה'
          });
        },
        error: () => {
          this.savingDishIds.delete(dishId);
          this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'לא ניתן לעדכן את סימון המתנה' });
        }
      });
  }

  toggleDish(step: WizardStep, dish: DishMenuMapping, isUpgrade: boolean): void {
    if (this.savingDishIds.has(dish.dish_id)) return;

    if (step.selectedDishIds.has(dish.dish_id)) {
      this.removeDish(step, dish);
    } else {
      this.addDish(step, dish, isUpgrade);
      // Show warning if quota exceeded
     
    }
  }

  private addDish(step: WizardStep, dish: DishMenuMapping, isUpgrade: boolean): void {
    const guestCount = this.event?.guest_count || 1;
    const servingSize = dish.dish_serving_size || 1;
    const quantity = Math.ceil(guestCount / servingSize);

    const payload: EventDishCreate = {
      dish_id: dish.dish_id,
      sub_meal_id: step.subMealId ?? undefined,
      category_id: step.categoryId,
      quantity,
      is_upgrade: isUpgrade,
      extra_charge: isUpgrade ? (dish.extra_charge ?? 0) : undefined
    };

    this.savingDishIds.add(dish.dish_id);

    this.eventService.addDishToEvent(this.eventId, payload).pipe(takeUntil(this.destroy$)).subscribe({
      next: updated => {
        this.event = updated;
        step.selectedDishIds.add(dish.dish_id);
        this.savingDishIds.delete(dish.dish_id);
      },
      error: () => {
        this.savingDishIds.delete(dish.dish_id);
        this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'לא ניתן להוסיף את המנה' });
      }
    });
  }

  private removeDish(step: WizardStep, dish: DishMenuMapping): void {
    this.savingDishIds.add(dish.dish_id);

    this.eventService.removeDishFromEvent(this.eventId, dish.dish_id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        step.selectedDishIds.delete(dish.dish_id);
        this.giftDishIds.delete(dish.dish_id);
        this.savingDishIds.delete(dish.dish_id);
      },
      error: () => {
        this.savingDishIds.delete(dish.dish_id);
        this.messageService.add({ severity: 'error', summary: 'שגיאה', detail: 'לא ניתן להסיר את המנה' });
      }
    });
  }

  // ========================================
  // Finish & Navigate
  // ========================================

  finishWizard(): void {
    this.router.navigate(['/events'], { queryParams: { openEvent: this.eventId } });
  }

  goBackToEvents(): void {
    this.router.navigate(['/events']);
  }

  // ========================================
  // Helpers
  // ========================================

  getSelectionLabel(step: WizardStep): string {
    const standardCount = this.getStandardDishCount(step);
    const giftCount = this.getGiftDishCount(step);
    const upgradeCount = step.selectedDishIds.size - standardCount - giftCount;
    if (step.quota) {
      const label = `${standardCount} / ${step.quota}`;
      const additions = [
        upgradeCount > 0 ? `${upgradeCount} שדרוגים` : '',
        giftCount > 0 ? `${giftCount} מתנה` : ''
      ].filter(Boolean).join(', ');
      return additions ? `${label} (+${additions})` : label;
    }
    const totalCount = step.selectedDishIds.size;
    return `${totalCount} נבחרו`;
  }

  getQuotaPercent(step: WizardStep): number {
    if (!step.quota) return 0;
    return Math.min(100, (this.getStandardDishCount(step) / step.quota) * 100);
  }

  getStepIcon(step: WizardStep): string {
    if (step.selectedDishIds.size === 0) return 'pi pi-circle';
    if (step.quota && this.getStandardDishCount(step) >= step.quota) return 'pi pi-check-circle';
    return 'pi pi-minus-circle';
  }

  getStepSeverity(step: WizardStep): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    if (step.selectedDishIds.size === 0) return 'secondary';
    if (step.quota && this.getStandardDishCount(step) >= step.quota) return 'success';
    return 'info';
  }

  getDishPrice(dish: DishMenuMapping): string {
    if (dish.dish_client_price) return `₪${dish.dish_client_price}`;
    return '';
  }

  /** Check if this step index starts a new sub-meal group */
  isSubMealBoundary(index: number): boolean {
    if (index === 0) return !!this.steps[0]?.subMealName;
    return this.steps[index]?.subMealId !== this.steps[index - 1]?.subMealId && !!this.steps[index]?.subMealName;
  }

  /** Get summary dishes for a step (needs dishes to be loaded) */
  getSelectedDishNames(step: WizardStep): string[] {
    const allDishes = [...step.standardDishes, ...step.upgradeDishes];
    return allDishes
      .filter(d => step.selectedDishIds.has(d.dish_id))
      .map(d => `${d.dish_name || `מנה #${d.dish_id}`}${this.isGiftDish(d.dish_id) ? ' 🎁' : ''}`);
  }

  /** For summary — load all steps that have selections but aren't loaded */
  loadAllForSummary(): void {
    const unloaded = this.steps.filter(s => !s.loaded && s.selectedDishIds.size > 0);
    if (unloaded.length === 0) return;
    const observables = unloaded.map(s => {
      s.loading = true;
      return this.menuService.getCategoryDishes(s.categoryId);
    });
    forkJoin(observables).pipe(takeUntil(this.destroy$)).subscribe({
      next: (results) => {
        results.forEach((response, i) => {
          const step = unloaded[i];
          step.standardDishes = response.standard_dishes || [];
          step.upgradeDishes = response.upgrade_dishes || [];
          step.loaded = true;
          step.loading = false;
        });
      }
    });
  }
}
