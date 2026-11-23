export interface ScannedItem {
  matched_product_id: number | null;
  name: string;
  edited_name: string;
  quantity: number;
  unit_price: number;
  is_new: boolean;
  current_stock: number;
  nameMatchLoading?: boolean;
}

export interface ExistingProduct {
  id: number;
  name: string;
  stock: number;
}

export interface ReceiptScanDialogData {
  existingProducts: ExistingProduct[];
  file?: File;
}

export interface ReceiptScanDialogResult {
  confirmed: boolean;
  items: ScannedItem[];
}