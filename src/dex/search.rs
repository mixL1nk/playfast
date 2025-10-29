use crate::dex::container::DexContainer;
use crate::dex::error::Result;
use crate::dex::filter::{ClassFilter, MethodFilter};
use crate::dex::models::{RustDexClass, RustDexMethod};

/// Search engine for finding classes and methods in DEX files
pub struct DexSearcher {
    container: DexContainer,
}

impl DexSearcher {
    /// Create a new DexSearcher
    pub fn new(container: DexContainer) -> Self {
        Self { container }
    }

    /// Find a single class matching the filter
    pub fn find_class(&self, filter: &ClassFilter) -> Result<Option<RustDexClass>> {
        let classes = self.container.extract_all_classes()?;

        for class in classes {
            if filter.matches(&class) {
                return Ok(Some(class));
            }
        }

        Ok(None)
    }

    /// Find all classes matching the filter
    pub fn find_classes(&self, filter: &ClassFilter, limit: Option<usize>) -> Result<Vec<RustDexClass>> {
        let classes = self.container.extract_all_classes()?;
        let mut results = Vec::new();

        for class in classes {
            if filter.matches(&class) {
                results.push(class);
                if let Some(max) = limit {
                    if results.len() >= max {
                        break;
                    }
                }
            }
        }

        Ok(results)
    }

    /// Find a single method matching the filters
    pub fn find_method(
        &self,
        class_filter: &ClassFilter,
        method_filter: &MethodFilter,
    ) -> Result<Option<RustDexMethod>> {
        let classes = self.find_classes(class_filter, None)?;

        for class in classes {
            for method in &class.methods {
                if method_filter.matches(method) {
                    return Ok(Some(method.clone()));
                }
            }
        }

        Ok(None)
    }

    /// Find all methods matching the filters
    pub fn find_methods(
        &self,
        class_filter: &ClassFilter,
        method_filter: &MethodFilter,
        limit: Option<usize>,
    ) -> Result<Vec<RustDexMethod>> {
        let classes = self.find_classes(class_filter, None)?;
        let mut results = Vec::new();

        for class in classes {
            for method in &class.methods {
                if method_filter.matches(method) {
                    results.push(method.clone());
                    if let Some(max) = limit {
                        if results.len() >= max {
                            return Ok(results);
                        }
                    }
                }
            }
        }

        Ok(results)
    }

    /// Get DEX file count
    pub fn dex_count(&self) -> usize {
        self.container.dex_count()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::apk::DexEntry;

    #[test]
    fn test_searcher_creation() {
        let entries = vec![DexEntry::new("classes.dex".to_string(), 0, vec![])];
        let container = DexContainer::new(entries);
        let searcher = DexSearcher::new(container);

        assert_eq!(searcher.dex_count(), 1);
    }
}
