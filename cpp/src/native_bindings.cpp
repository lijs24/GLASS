#include <cuda_runtime.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <cmath>
#include <limits>
#include <algorithm>
#include <array>
#include <utility>
#include <chrono>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <thread>
#include <atomic>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <cctype>

namespace py = pybind11;

struct CudaFloatFree {
  void operator()(float* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFree(ptr);
    }
  }
};

struct CudaUCharFree {
  void operator()(unsigned char* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFree(ptr);
    }
  }
};

struct CudaHostUCharFree {
  void operator()(unsigned char* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFreeHost(ptr);
    }
  }
};

struct CudaUllFree {
  void operator()(unsigned long long* ptr) const noexcept {
    if (ptr != nullptr) {
      (void)cudaFree(ptr);
    }
  }
};

void glass_smoke_add_f32_launch(const float* a, const float* b, float* out, std::size_t n);
void glass_calibrate_tile_f32_launch(
    const float* light,
    const float* bias,
    const float* dark,
    const float* flat,
    float* out,
    std::size_t n,
    bool has_bias,
    bool has_dark,
    bool has_flat,
    bool master_dark_includes_bias,
    float dark_scale,
    float flat_floor,
    float pedestal);
void glass_calibrate_tile_f32_launch_stream(
    const float* light,
    const float* bias,
    const float* dark,
    const float* flat,
    float* out,
    std::size_t n,
    bool has_bias,
    bool has_dark,
    bool has_flat,
    bool master_dark_includes_bias,
    float dark_scale,
    float flat_floor,
    float pedestal,
    cudaStream_t stream);
void glass_calibrate_fits_u16be_bzero_f32_launch_stream(
    const unsigned char* raw_be,
    const float* bias,
    const float* dark,
    const float* flat,
    float* out,
    std::size_t n,
    bool has_bias,
    bool has_dark,
    bool has_flat,
    bool master_dark_includes_bias,
    float dark_scale,
    float flat_floor,
    float pedestal,
    cudaStream_t stream);
void glass_mean_stack_tiles_f32_launch(
    const float* stack, float* out, std::size_t frame_count, std::size_t pixels_per_frame);
void glass_warp_translation_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    int dx,
    int dy,
    float fill,
    float* coverage_accumulator);
void glass_warp_translation_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    int width,
    int height,
    float dx,
    float dy,
    float fill,
    float* coverage_accumulator);
void glass_warp_matrix_bilinear_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill,
    float* coverage_accumulator);
void glass_warp_matrix_lanczos3_f32_launch(
    const float* input,
    float* output,
    float* coverage,
    const float* inverse,
    int width,
    int height,
    float fill,
    float clamping_threshold,
    float* coverage_accumulator);
void glass_warp_matrix_bilinear_batch_f32_launch(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill);
void glass_warp_matrix_bilinear_batch_f32_launch_stream(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill,
    cudaStream_t stream);
void glass_warp_matrix_lanczos3_batch_f32_launch(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill,
    float clamping_threshold);
void glass_warp_matrix_lanczos3_batch_f32_launch_stream(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill,
    float clamping_threshold,
    cudaStream_t stream);
void glass_warp_matrix_lanczos3_batch_unclamped_f32_launch(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill);
void glass_warp_matrix_lanczos3_batch_unclamped_f32_launch_stream(
    const float* stack,
    float* batch_output,
    unsigned char* batch_coverage,
    const unsigned long long* frame_indices,
    const float* inverses,
    int frame_count,
    int width,
    int height,
    float fill,
    cudaStream_t stream);
void glass_warp_batch_coverage_reduce_f32_launch(
    const unsigned char* batch_coverage,
    float* coverage_accumulator,
    int frame_count,
    std::size_t pixels_per_frame);
void glass_warp_batch_scatter_f32_launch(
    const float* batch_output,
    float* stack,
    const unsigned long long* frame_indices,
    int frame_count,
    std::size_t pixels_per_frame);
void glass_warp_batch_scatter_f32_launch_stream(
    const float* batch_output,
    float* stack,
    const unsigned long long* frame_indices,
    int frame_count,
    std::size_t pixels_per_frame,
    cudaStream_t stream);
void glass_warp_batch_scatter_reduce_f32_launch(
    const float* batch_output,
    const unsigned char* batch_coverage,
    float* stack,
    float* coverage_accumulator,
    const unsigned long long* frame_indices,
    int frame_count,
    std::size_t pixels_per_frame);
void glass_warp_batch_scatter_reduce_f32_launch_stream(
    const float* batch_output,
    const unsigned char* batch_coverage,
    float* stack,
    float* coverage_accumulator,
    const unsigned long long* frame_indices,
    int frame_count,
    std::size_t pixels_per_frame,
    cudaStream_t stream);
void glass_coverage_accumulate_f32_launch(const float* coverage, float* accumulator, std::size_t n);
void glass_coverage_accumulate_full_f32_launch(float* accumulator, std::size_t n);
void glass_matrix_alignment_metrics_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverse,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int blocks);
void glass_matrix_alignment_metrics_candidates_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverses,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int candidate_count);
void glass_matrix_alignment_metrics_batch_candidates_f32_launch(
    const float* reference,
    const float* stack,
    const int* moving_frame_indices,
    unsigned long long pixels_per_frame,
    const float* inverses,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int sample_stride,
    int candidate_count);
void glass_star_core_metrics_candidates_f32_launch(
    const float* reference,
    const float* moving,
    const float* inverses,
    float threshold,
    double* partial_stats,
    unsigned long long* partial_count,
    int width,
    int height,
    int candidate_count);
void glass_estimate_translation_search_f32_launch(
    const float* reference,
    const float* moving,
    float* scores,
    int* best_dx,
    int* best_dy,
    float* best_score,
    int width,
    int height,
    int max_shift_x,
    int max_shift_y,
    int sample_stride);
void glass_estimate_translation_subpixel_ncc_f32_launch(
    const float* reference,
    const float* moving,
    float* scores,
    float* best_dx,
    float* best_dy,
    float* best_score,
    int width,
    int height,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int sample_stride);
void glass_estimate_translation_from_catalogs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_dx,
    float* candidate_dy,
    int* scores,
    float* best_dx,
    float* best_dy,
    int* best_inliers,
    int* moving_best_reference,
    int* reference_best_moving,
    float* refine_sums,
    int* mutual_inliers,
    float* refined_dx,
    float* refined_dy,
    float* rms_px,
    int reference_count,
    int moving_count,
    float tolerance_px,
    float max_abs_dx,
    float max_abs_dy,
    float prior_dx,
    float prior_dy,
    float prior_radius_px);
void glass_triangle_asterism_descriptors_f32_launch(
    const float* x,
    const float* y,
    float* descriptors,
    int* indices,
    float* areas,
    unsigned char* valid,
    int count,
    int neighbors,
    int raw_count);
void glass_triangle_asterism_descriptors_batch_f32_launch(
    const float* x_batch,
    const float* y_batch,
    float* descriptors,
    int* indices,
    float* areas,
    unsigned char* valid,
    const int* counts,
    const int* neighbors_by_frame,
    const int* combos_by_frame,
    int batch_count,
    int max_count,
    int raw_capacity);
void glass_estimate_similarity_from_triangle_descriptors_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    const float* reference_descriptors,
    const int* reference_indices,
    const float* moving_descriptors,
    const int* moving_indices,
    float* candidate_params,
    int* candidate_scores,
    float* candidate_rms,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* best_inliers,
    int* best_index,
    int reference_count,
    int moving_count,
    int reference_descriptor_count,
    int moving_descriptor_count,
    int candidate_count,
    float tolerance_px,
    float descriptor_radius);
void glass_estimate_similarity_from_pairs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* valid_count,
    int* status,
    double* partial_sums,
    unsigned long long* partial_count,
    double* partial_residual_sums,
    int count,
    int blocks);
void glass_estimate_similarity_from_catalogs_f32_launch(
    const float* reference_x,
    const float* reference_y,
    const float* moving_x,
    const float* moving_y,
    float* candidate_params,
    int* candidate_scores,
    float* candidate_rms,
    float* matrix,
    float* scale,
    float* rotation_rad,
    float* rms_px,
    int* best_inliers,
    int* best_index,
    int* refit_inliers,
    int* refit_status,
    float* refit_matrix,
    float* refit_scale,
    float* refit_rotation_rad,
    float* refit_rms_px,
    double* refit_partial_sums,
    unsigned long long* refit_partial_count,
    double* refit_partial_residual_sums,
    int refit_blocks,
    int reference_count,
    int moving_count,
    int candidate_count,
    float tolerance_px,
    float min_pair_distance,
    float prior_dx,
    float prior_dy,
    float prior_radius_px,
    float min_scale,
    float max_scale,
    float max_abs_rotation_rad);
void glass_local_norm_apply_f32_launch(
    const float* input, float* output, std::size_t n, float scale, float offset);
void glass_local_norm_apply_grid_f32_launch(
    const float* input,
    float* output,
    const float* scales,
    const float* offsets,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows);
void glass_frame_sum_stats_f32_launch(
    const float* input,
    double* partial_sum,
    double* partial_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void glass_pair_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* partial_source_sum,
    double* partial_source_sum2,
    double* partial_reference_sum,
    double* partial_reference_sum2,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void glass_pair_grid_sum_stats_f32_launch(
    const float* source,
    const float* reference,
    double* source_sum,
    double* source_sum2,
    double* reference_sum,
    double* reference_sum2,
    unsigned long long* count,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows);
void glass_pair_grid_sum_stats_batch_f32_launch(
    const float* stack,
    const int* source_indices,
    int source_count,
    int reference_index,
    double* source_sum,
    double* source_sum2,
    double* reference_sum,
    double* reference_sum2,
    unsigned long long* count,
    std::size_t pixels_per_frame,
    int width,
    int height,
    int tile_width,
    int tile_height,
    int grid_cols,
    int grid_rows);
void glass_integrate_accumulate_mean_tile_f32_launch(
    const float* frame, const float* weight, float* sum, float* weight_sum, std::size_t n);
void glass_apply_invalid_mask_f32_launch(
    float* frame, const unsigned char* invalid_mask, std::size_t n);
void glass_apply_cosmetic_threshold_mask_f32_launch(
    float* frame,
    std::size_t n,
    float low_threshold,
    float high_threshold,
    unsigned long long* counts);
void glass_count_cosmetic_threshold_mask_f32_launch(
    const float* frame,
    std::size_t n,
    float low_threshold,
    float high_threshold,
    unsigned long long* counts);
void glass_apply_cosmetic_threshold_mask_frames_f32_launch(
    float* stack,
    std::size_t n,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    std::size_t frame_count,
    unsigned long long* counts);
void glass_count_cosmetic_threshold_mask_frames_f32_launch(
    const float* stack,
    std::size_t n,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    std::size_t frame_count,
    unsigned long long* counts);
void glass_apply_isolated_cosmetic_threshold_mask_f32_launch(
    float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts);
void glass_count_isolated_cosmetic_threshold_mask_f32_launch(
    const float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts);
void glass_apply_isolated_cosmetic_threshold_mask_frames_f32_launch(
    float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts);
void glass_count_isolated_cosmetic_threshold_mask_frames_f32_launch(
    const float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts);
void glass_apply_star_protected_isolated_cosmetic_threshold_mask_f32_launch(
    float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    const float* star_xs,
    const float* star_ys,
    int star_count,
    float star_protection_radius,
    unsigned long long* counts);
void glass_count_star_protected_isolated_cosmetic_threshold_mask_f32_launch(
    const float* frame,
    std::size_t width,
    std::size_t height,
    float low_threshold,
    float high_threshold,
    float median,
    float sigma,
    float structure_sigma,
    int min_neighbor_support,
    const float* star_xs,
    const float* star_ys,
    int star_count,
    float star_protection_radius,
    unsigned long long* counts);
void glass_apply_star_protected_isolated_cosmetic_threshold_mask_frames_f32_launch(
    float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    const unsigned long long* star_offsets,
    const unsigned long long* star_counts,
    const float* star_xs,
    const float* star_ys,
    const float* star_protection_radii,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts);
void glass_count_star_protected_isolated_cosmetic_threshold_mask_frames_f32_launch(
    const float* stack,
    std::size_t width,
    std::size_t height,
    const unsigned long long* frame_indices,
    const float* low_thresholds,
    const float* high_thresholds,
    const float* medians,
    const float* sigmas,
    const unsigned long long* star_offsets,
    const unsigned long long* star_counts,
    const float* star_xs,
    const float* star_ys,
    const float* star_protection_radii,
    std::size_t frame_count,
    float structure_sigma,
    int min_neighbor_support,
    unsigned long long* counts);
void glass_sample_frame_even_f32_launch(
    const float* frame,
    float* sample,
    std::size_t n,
    std::size_t sample_count);
void glass_frame_minmax_count_f32_launch(
    const float* frame,
    float* partial_min,
    float* partial_max,
    unsigned long long* partial_count,
    std::size_t n,
    int blocks);
void glass_frame_histogram_f32_launch(
    const float* frame,
    unsigned long long* histogram,
    std::size_t n,
    float min_value,
    float inv_bin_width,
    int bin_count,
    int blocks);
void glass_frame_absdev_histogram_f32_launch(
    const float* frame,
    unsigned long long* histogram,
    std::size_t n,
    float center,
    float inv_bin_width,
    int bin_count,
    int blocks);
void glass_integrate_resident_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame);
void glass_integrate_resident_tile_local_weighted_mean_f32_launch(
    const float* stack,
    const float* weights,
    const unsigned char* target_mask,
    const int* tile_extents,
    const float* tile_multipliers,
    float* master,
    float* weight_map,
    std::size_t frame_count,
    int width,
    int height,
    int tile_count);
void glass_integrate_resident_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    bool winsorize);
void glass_integrate_resident_hardened_winsorized_sigma_f32_launch(
    const float* stack,
    const float* weights,
    const unsigned int* active_indices,
    const unsigned char* unit_positive_weight_mask,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t active_frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction,
    bool unit_positive_weights,
    bool unit_positive_weight_mask_enabled,
    bool unit_positive_local_reuse,
    bool unit_positive_selected_reuse);
void glass_integrate_resident_hardened_winsorized_sigma_f32_u16_counts_launch(
    const float* stack,
    const float* weights,
    const unsigned int* active_indices,
    const unsigned char* unit_positive_weight_mask,
    float* master,
    float* weight_map,
    unsigned short* coverage_map,
    unsigned short* low_rejection_map,
    unsigned short* high_rejection_map,
    std::size_t frame_count,
    std::size_t active_frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction,
    bool unit_positive_weights,
    bool unit_positive_weight_mask_enabled,
    bool unit_positive_local_reuse,
    bool unit_positive_selected_reuse);
void glass_integrate_resident_hardened_winsorized_sigma_f32_radix_select_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction);
void glass_integrate_resident_hardened_winsorized_sigma_f32_radix_select_u16_counts_launch(
    const float* stack,
    const float* weights,
    float* master,
    float* weight_map,
    unsigned short* coverage_map,
    unsigned short* low_rejection_map,
    unsigned short* high_rejection_map,
    std::size_t frame_count,
    std::size_t pixels_per_frame,
    float low_sigma,
    float high_sigma,
    int min_samples,
    float max_reject_fraction);
void glass_integrate_resident_tile_local_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    const unsigned char* target_mask,
    const int* tile_extents,
    const float* tile_multipliers,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    std::size_t frame_count,
    int width,
    int height,
    int tile_count,
    float low_sigma,
    float high_sigma,
    bool winsorize);
void glass_integrate_matrix_warped_mean_f32_launch(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold);
void glass_integrate_matrix_warped_sigma_clip_f32_launch(
    const float* stack,
    const float* weights,
    const float* inverses,
    float* master,
    float* weight_map,
    float* coverage_map,
    float* low_rejection_map,
    float* high_rejection_map,
    float* geometric_coverage_map,
    std::size_t frame_count,
    int width,
    int height,
    int interpolation,
    float clamping_threshold,
    float low_sigma,
    float high_sigma,
    bool winsorize);
void glass_star_local_max_mask_f32_launch(
    const float* input,
    unsigned char* mask,
    int width,
    int height,
    float threshold);
void glass_star_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int width,
    int height,
    float threshold,
    int max_candidates);
void glass_star_top_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* lock,
    int width,
    int height,
    float threshold,
    int max_candidates);
void glass_star_top_nms_candidates_f32_launch(
    const float* input,
    float* scan_xs,
    float* scan_ys,
    float* scan_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* lock,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int scan_candidates,
    int max_output_candidates,
    float min_separation_px);
void glass_star_grid_top_nms_candidates_f32_launch(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* locks,
    int* cell_counts,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px);
void glass_star_grid_top_nms_candidates_f32_launch_stream(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* locks,
    int* cell_counts,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px,
    cudaStream_t stream);
void glass_star_grid_top_nms_candidates_deterministic_f32_launch(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px);
void glass_star_grid_top_nms_candidates_deterministic_f32_launch_stream(
    const float* input,
    float* grid_xs,
    float* grid_ys,
    float* grid_fluxes,
    float* out_xs,
    float* out_ys,
    float* out_fluxes,
    int* count,
    int* stored_count,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px,
    cudaStream_t stream);
void glass_star_refine_centroids_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    unsigned char* statuses,
    int count,
    int width,
    int height,
    int radius,
    float background_override);
void glass_star_refine_centroids_f32_launch_stream(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    unsigned char* statuses,
    int count,
    int width,
    int height,
    int radius,
    float background_override,
    cudaStream_t stream);
void glass_frame_sum_f32_launch(
    const float* input,
    double* partial_sums,
    unsigned int* partial_counts,
    std::size_t n,
    int blocks);
void glass_frame_sum_f32_launch_stream(
    const float* input,
    double* partial_sums,
    unsigned int* partial_counts,
    std::size_t n,
    int blocks,
    cudaStream_t stream);
void glass_star_grid_candidates_f32_launch(
    const float* input,
    float* xs,
    float* ys,
    float* fluxes,
    int* count,
    int* locks,
    int width,
    int height,
    float threshold,
    int grid_cols,
    int grid_rows);

namespace {

void check_cuda(cudaError_t status, const char* operation) {
  if (status == cudaSuccess) {
    return;
  }
  std::ostringstream message;
  message << operation << " failed: " << cudaGetErrorString(status);
  throw std::runtime_error(message.str());
}

std::size_t element_count(const py::buffer_info& info) {
  std::size_t n = 1;
  for (const auto dim : info.shape) {
    n *= static_cast<std::size_t>(dim);
  }
  return n;
}

float device_frame_mean_f32(const float* device_input, std::size_t n, const char* label) {
  if (n == 0) {
    return std::numeric_limits<float>::quiet_NaN();
  }
  constexpr int threads = 256;
  const int blocks = static_cast<int>(
      std::min<std::size_t>(4096, std::max<std::size_t>(1, (n + threads - 1) / threads)));
  double* d_sums = nullptr;
  unsigned int* d_counts = nullptr;
  try {
    check_cuda(cudaMalloc(&d_sums, static_cast<std::size_t>(blocks) * sizeof(double)), label);
    check_cuda(cudaMalloc(&d_counts, static_cast<std::size_t>(blocks) * sizeof(unsigned int)), label);
    glass_frame_sum_f32_launch(device_input, d_sums, d_counts, n, blocks);
    check_cuda(cudaGetLastError(), "frame mean reduction kernel launch");
    check_cuda(cudaDeviceSynchronize(), "frame mean reduction synchronize");
    std::vector<double> sums(static_cast<std::size_t>(blocks));
    std::vector<unsigned int> counts(static_cast<std::size_t>(blocks));
    check_cuda(
        cudaMemcpy(sums.data(), d_sums, static_cast<std::size_t>(blocks) * sizeof(double), cudaMemcpyDeviceToHost),
        "cudaMemcpy(frame mean sums)");
    check_cuda(
        cudaMemcpy(
            counts.data(),
            d_counts,
            static_cast<std::size_t>(blocks) * sizeof(unsigned int),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(frame mean counts)");
    cudaFree(d_sums);
    cudaFree(d_counts);
    d_sums = nullptr;
    d_counts = nullptr;
    double sum = 0.0;
    std::size_t count = 0;
    for (int i = 0; i < blocks; ++i) {
      sum += sums[static_cast<std::size_t>(i)];
      count += static_cast<std::size_t>(counts[static_cast<std::size_t>(i)]);
    }
    if (count == 0) {
      return std::numeric_limits<float>::quiet_NaN();
    }
    return static_cast<float>(sum / static_cast<double>(count));
  } catch (...) {
    cudaFree(d_sums);
    cudaFree(d_counts);
    throw;
  }
}

void require_same_shape(const py::buffer_info& a, const py::buffer_info& b) {
  if (a.shape != b.shape) {
    throw std::invalid_argument("input arrays must have the same shape");
  }
}

bool dict_bool(const py::dict& dict, const char* key, bool fallback) {
  if (!dict.contains(key)) {
    return fallback;
  }
  return py::cast<bool>(dict[key]);
}

float dict_float(const py::dict& dict, const char* key, float fallback) {
  if (!dict.contains(key)) {
    return fallback;
  }
  return py::cast<float>(dict[key]);
}

int dict_int(const py::dict& dict, const char* key, int fallback) {
  if (!dict.contains(key)) {
    return fallback;
  }
  return py::cast<int>(dict[key]);
}

std::string dict_string(const py::dict& dict, const char* key, const char* fallback) {
  if (!dict.contains(key)) {
    return std::string(fallback);
  }
  return py::cast<std::string>(dict[key]);
}

using Clock = std::chrono::steady_clock;

double seconds_since(const Clock::time_point& start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}

std::string glass_get_env_string(const char* name) {
#ifdef _MSC_VER
  char* env_buffer = nullptr;
  std::size_t env_length = 0;
  std::string value;
  if (_dupenv_s(&env_buffer, &env_length, name) == 0 && env_buffer != nullptr) {
    value = env_buffer;
    std::free(env_buffer);
  }
  return value;
#else
  const char* value = std::getenv(name);
  return value == nullptr ? std::string() : std::string(value);
#endif
}

std::string glass_lower_ascii(std::string value) {
  std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
    return static_cast<char>(std::tolower(c));
  });
  return value;
}

bool glass_env_flag_enabled_strict(const std::string& value) {
  const std::string lowered = glass_lower_ascii(value);
  return lowered == "1" || lowered == "true" || lowered == "yes" || lowered == "on";
}

std::string glass_env_flag_reason_strict(const std::string& value) {
  if (value.empty()) {
    return "disabled";
  }
  if (glass_env_flag_enabled_strict(value)) {
    return "environment_enabled";
  }
  const std::string lowered = glass_lower_ascii(value);
  if (lowered == "0" || lowered == "false" || lowered == "no" || lowered == "off") {
    return "environment_disabled";
  }
  return "ignored_unrecognized_env_value";
}

double sorted_median_f32(std::vector<float>& values) {
  if (values.empty()) {
    return 0.0;
  }
  std::sort(values.begin(), values.end());
  const std::size_t mid = values.size() / 2;
  if ((values.size() % 2) != 0) {
    return static_cast<double>(values[mid]);
  }
  return (static_cast<double>(values[mid - 1]) + static_cast<double>(values[mid])) * 0.5;
}

double histogram_quantile_center(
    const std::vector<unsigned long long>& histogram,
    unsigned long long count,
    double min_value,
    double bin_width,
    double quantile) {
  if (histogram.empty() || count == 0 || !(bin_width > 0.0)) {
    return min_value;
  }
  double q = quantile;
  if (q < 0.0) {
    q = 0.0;
  } else if (q > 1.0) {
    q = 1.0;
  }
  auto center_for_rank = [&](unsigned long long rank) {
    const unsigned long long target = rank + 1ULL;
    unsigned long long cumulative = 0ULL;
    for (std::size_t i = 0; i < histogram.size(); ++i) {
      cumulative += histogram[i];
      if (cumulative >= target) {
        return min_value + (static_cast<double>(i) + 0.5) * bin_width;
      }
    }
    return min_value + (static_cast<double>(histogram.size()) - 0.5) * bin_width;
  };
  const double raw_rank = q * static_cast<double>(count - 1ULL);
  const auto low_rank = static_cast<unsigned long long>(std::floor(raw_rank));
  const auto high_rank = static_cast<unsigned long long>(std::ceil(raw_rank));
  const double low_center = center_for_rank(low_rank);
  if (high_rank == low_rank) {
    return low_center;
  }
  const double high_center = center_for_rank(high_rank);
  const double fraction = raw_rank - static_cast<double>(low_rank);
  return low_center + (high_center - low_center) * fraction;
}

const char* grid_catalog_sort_mode(int grid_capacity) {
  return grid_capacity <= 4096 ? "shared_bitonic_power2" : "single_thread_selection";
}

const char* grid_catalog_topk_mode(bool deterministic = false, int candidates_per_cell = 0) {
  if (!deterministic) {
    return "strict_flux_precheck_per_cell_lock";
  }
  return candidates_per_cell <= 16 ? "deterministic_parallel_per_cell" : "deterministic_serial_per_cell";
}

py::dict centroid_refine_summary(
    int centroid_radius,
    int stored_count,
    const std::vector<float>& before_xs,
    const std::vector<float>& before_ys,
    const float* after_xs,
    const float* after_ys,
    const std::vector<unsigned char>& statuses) {
  int refined_count = 0;
  int failed_count = 0;
  double max_shift_px = 0.0;
  if (centroid_radius > 0) {
    for (int i = 0; i < stored_count; ++i) {
      const bool refined =
          i < static_cast<int>(statuses.size()) && statuses[static_cast<std::size_t>(i)] != 0;
      if (!refined) {
        ++failed_count;
        continue;
      }
      ++refined_count;
      if (i < static_cast<int>(before_xs.size()) && i < static_cast<int>(before_ys.size())) {
        const double dx = static_cast<double>(after_xs[i]) - static_cast<double>(before_xs[static_cast<std::size_t>(i)]);
        const double dy = static_cast<double>(after_ys[i]) - static_cast<double>(before_ys[static_cast<std::size_t>(i)]);
        max_shift_px = std::max(max_shift_px, std::hypot(dx, dy));
      }
    }
  }
  py::dict summary;
  summary["enabled"] = centroid_radius > 0;
  summary["mode"] = centroid_radius > 0 ? "resident_gpu_window_centroid" : "off";
  summary["radius"] = centroid_radius;
  summary["stored_count"] = stored_count;
  summary["refined_count"] = refined_count;
  summary["failed_count"] = failed_count;
  summary["max_shift_px"] = static_cast<float>(max_shift_px);
  return summary;
}

struct CalibrationParameters {
  bool master_dark_includes_bias = true;
  bool dark_scaling_enabled = true;
  float flat_floor = 1.0e-6f;
  float pedestal = 0.0f;
  float dark_scale = 1.0f;
};

struct ResidentCalibrationTiming {
  double host_copy_s = 0.0;
  double h2d_s = 0.0;
  double calibrate_store_s = 0.0;
  double total_s = 0.0;
};

class CudaEvent {
 public:
  explicit CudaEvent(const char* operation) {
    check_cuda(cudaEventCreate(&event_), operation);
  }

  CudaEvent(const CudaEvent&) = delete;
  CudaEvent& operator=(const CudaEvent&) = delete;

  ~CudaEvent() {
    if (event_ != nullptr) {
      cudaEventDestroy(event_);
    }
  }

  cudaEvent_t get() const { return event_; }

 private:
  cudaEvent_t event_ = nullptr;
};

class CudaStream {
 public:
  explicit CudaStream(const char* operation) {
    check_cuda(cudaStreamCreate(&stream_), operation);
  }

  CudaStream(const CudaStream&) = delete;
  CudaStream& operator=(const CudaStream&) = delete;

  ~CudaStream() {
    if (stream_ != nullptr) {
      cudaStreamDestroy(stream_);
    }
  }

  cudaStream_t get() const { return stream_; }

 private:
  cudaStream_t stream_ = nullptr;
};

double cuda_event_elapsed_s(const CudaEvent& start, const CudaEvent& stop, const char* operation) {
  float elapsed_ms = 0.0f;
  check_cuda(cudaEventElapsedTime(&elapsed_ms, start.get(), stop.get()), operation);
  return static_cast<double>(elapsed_ms) / 1000.0;
}

double cuda_event_elapsed_s(cudaEvent_t start, cudaEvent_t stop, const char* operation) {
  float elapsed_ms = 0.0f;
  check_cuda(cudaEventElapsedTime(&elapsed_ms, start, stop), operation);
  return static_cast<double>(elapsed_ms) / 1000.0;
}

void require_frame_shape(const py::buffer_info& info, std::size_t height, std::size_t width) {
  if (info.ndim != 2) {
    throw std::invalid_argument("frame must have shape (height, width)");
  }
  if (static_cast<std::size_t>(info.shape[0]) != height ||
      static_cast<std::size_t>(info.shape[1]) != width) {
      throw std::invalid_argument("frame shape does not match the resident stack");
  }
}

std::array<float, 9> parse_matrix3x3(py::object matrix_obj) {
  auto matrix = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(matrix_obj);
  if (!matrix) {
    throw std::invalid_argument("matrix must be convertible to a float32 array");
  }
  const py::buffer_info info = matrix.request();
  if (info.ndim != 2 || info.shape[0] != 3 || info.shape[1] != 3) {
    throw std::invalid_argument("matrix must have shape (3, 3)");
  }
  const auto* values = static_cast<const float*>(info.ptr);
  std::array<float, 9> out{};
  for (std::size_t i = 0; i < out.size(); ++i) {
    out[i] = values[i];
  }
  return out;
}

py::list matrix3x3_to_pylist(const std::array<float, 9>& matrix) {
  py::list rows;
  for (int row = 0; row < 3; ++row) {
    py::list values;
    for (int col = 0; col < 3; ++col) {
      values.append(matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    rows.append(values);
  }
  return rows;
}

std::vector<std::array<float, 9>> parse_matrix_stack(py::object matrices_obj) {
  auto matrices = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(matrices_obj);
  if (!matrices) {
    throw std::invalid_argument("matrices must be convertible to a float32 array");
  }
  const py::buffer_info info = matrices.request();
  if (info.ndim == 2 && info.shape[0] == 3 && info.shape[1] == 3) {
    return {parse_matrix3x3(matrices)};
  }
  if (info.ndim != 3 || info.shape[1] != 3 || info.shape[2] != 3) {
    throw std::invalid_argument("matrices must have shape (N, 3, 3) or (3, 3)");
  }
  if (info.shape[0] <= 0) {
    throw std::invalid_argument("matrices must contain at least one matrix");
  }
  const auto* values = static_cast<const float*>(info.ptr);
  std::vector<std::array<float, 9>> out(static_cast<std::size_t>(info.shape[0]));
  for (std::size_t matrix_index = 0; matrix_index < out.size(); ++matrix_index) {
    for (std::size_t value_index = 0; value_index < 9; ++value_index) {
      out[matrix_index][value_index] = values[matrix_index * 9 + value_index];
    }
  }
  return out;
}

std::vector<std::size_t> parse_index_sequence(py::object indices_obj, const char* name) {
  auto indices = py::array_t<long long, py::array::c_style | py::array::forcecast>::ensure(indices_obj);
  if (!indices) {
    throw std::invalid_argument(std::string(name) + " must be convertible to an int64 array");
  }
  const py::buffer_info info = indices.request();
  if (info.ndim != 1) {
    throw std::invalid_argument(std::string(name) + " must be one-dimensional");
  }
  const auto* values = static_cast<const long long*>(info.ptr);
  std::vector<std::size_t> out(static_cast<std::size_t>(info.shape[0]));
  for (std::size_t i = 0; i < out.size(); ++i) {
    if (values[i] < 0) {
      throw std::invalid_argument(std::string(name) + " must not contain negative frame indices");
    }
    out[i] = static_cast<std::size_t>(values[i]);
  }
  return out;
}

std::vector<float> parse_float_sequence(py::object values_obj, const char* name) {
  auto values = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(values_obj);
  if (!values) {
    throw std::invalid_argument(std::string(name) + " must be convertible to a float32 array");
  }
  const py::buffer_info info = values.request();
  if (info.ndim != 1) {
    throw std::invalid_argument(std::string(name) + " must be one-dimensional");
  }
  const auto* ptr = static_cast<const float*>(info.ptr);
  return std::vector<float>(ptr, ptr + static_cast<std::size_t>(info.shape[0]));
}

std::array<float, 9> invert_matrix3x3(const std::array<float, 9>& m) {
  const double a = m[0];
  const double b = m[1];
  const double c = m[2];
  const double d = m[3];
  const double e = m[4];
  const double f = m[5];
  const double g = m[6];
  const double h = m[7];
  const double i = m[8];
  const double c00 = e * i - f * h;
  const double c01 = -(d * i - f * g);
  const double c02 = d * h - e * g;
  const double c10 = -(b * i - c * h);
  const double c11 = a * i - c * g;
  const double c12 = -(a * h - b * g);
  const double c20 = b * f - c * e;
  const double c21 = -(a * f - c * d);
  const double c22 = a * e - b * d;
  const double det = a * c00 + b * c01 + c * c02;
  if (std::abs(det) <= 1.0e-20) {
    throw std::invalid_argument("matrix must be invertible");
  }
  const double inv_det = 1.0 / det;
  return {
      static_cast<float>(c00 * inv_det),
      static_cast<float>(c10 * inv_det),
      static_cast<float>(c20 * inv_det),
      static_cast<float>(c01 * inv_det),
      static_cast<float>(c11 * inv_det),
      static_cast<float>(c21 * inv_det),
      static_cast<float>(c02 * inv_det),
      static_cast<float>(c12 * inv_det),
      static_cast<float>(c22 * inv_det)};
}

struct MatrixCandidateMetrics {
  float dx = 0.0f;
  float dy = 0.0f;
  std::array<float, 9> matrix{};
  unsigned long long valid_pixels = 0ULL;
  int sampled_pixels = 0;
  int sample_stride = 1;
  double rms = std::numeric_limits<double>::quiet_NaN();
  double mean_abs_diff = std::numeric_limits<double>::quiet_NaN();
  double ncc = std::numeric_limits<double>::quiet_NaN();
};

struct MatrixRefineWorkspace {
  float* d_inverses = nullptr;
  double* d_partial_stats = nullptr;
  unsigned long long* d_partial_count = nullptr;
  int* d_moving_frame_indices = nullptr;
  int candidate_capacity = 0;
};

std::size_t matrix_refine_workspace_bytes(int candidate_capacity) {
  if (candidate_capacity <= 0) {
    return 0;
  }
  return static_cast<std::size_t>(candidate_capacity) * 9 * sizeof(float) +
         static_cast<std::size_t>(candidate_capacity) * 7 * sizeof(double) +
         static_cast<std::size_t>(candidate_capacity) * sizeof(unsigned long long) +
         static_cast<std::size_t>(candidate_capacity) * sizeof(int);
}

std::vector<std::pair<float, float>> translation_offsets(
    float center_dx,
    float center_dy,
    float radius,
    float step) {
  if (radius < 0.0f) {
    throw std::invalid_argument("search radius must be non-negative");
  }
  if (step <= 0.0f) {
    throw std::invalid_argument("search step must be positive");
  }
  std::vector<std::pair<float, float>> offsets;
  for (float dx = center_dx - radius; dx <= center_dx + radius + step * 0.5f; dx += step) {
    for (float dy = center_dy - radius; dy <= center_dy + radius + step * 0.5f; dy += step) {
      offsets.emplace_back(dx, dy);
    }
  }
  if (offsets.empty()) {
    offsets.emplace_back(center_dx, center_dy);
  }
  return offsets;
}

MatrixCandidateMetrics metrics_from_sums(
    const std::array<float, 9>& matrix,
    float dx,
    float dy,
    const double* sums,
    unsigned long long valid_pixels,
    int sampled_pixels,
    int sample_stride) {
  MatrixCandidateMetrics metrics;
  metrics.dx = dx;
  metrics.dy = dy;
  metrics.matrix = matrix;
  metrics.valid_pixels = valid_pixels;
  metrics.sampled_pixels = sampled_pixels;
  metrics.sample_stride = sample_stride;
  if (valid_pixels == 0ULL) {
    return metrics;
  }
  const double count = static_cast<double>(valid_pixels);
  metrics.rms = std::sqrt(sums[5] / count);
  metrics.mean_abs_diff = sums[6] / count;
  if (valid_pixels > 1ULL) {
    const double numerator = sums[4] - (sums[0] * sums[1] / count);
    const double ref_var = std::max(sums[2] - (sums[0] * sums[0] / count), 0.0);
    const double mov_var = std::max(sums[3] - (sums[1] * sums[1] / count), 0.0);
    const double denominator = std::sqrt(ref_var * mov_var);
    if (denominator > 0.0) {
      metrics.ncc = numerator / denominator;
    }
  }
  return metrics;
}

bool better_matrix_metric(const MatrixCandidateMetrics& candidate, const MatrixCandidateMetrics& current) {
  const bool candidate_rms_finite = std::isfinite(candidate.rms);
  const bool current_rms_finite = std::isfinite(current.rms);
  if (candidate_rms_finite != current_rms_finite) {
    return candidate_rms_finite;
  }
  if (candidate_rms_finite && std::abs(candidate.rms - current.rms) > 1.0e-12) {
    return candidate.rms < current.rms;
  }
  const bool candidate_ncc_finite = std::isfinite(candidate.ncc);
  const bool current_ncc_finite = std::isfinite(current.ncc);
  if (candidate_ncc_finite != current_ncc_finite) {
    return candidate_ncc_finite;
  }
  if (candidate_ncc_finite && std::abs(candidate.ncc - current.ncc) > 1.0e-12) {
    return candidate.ncc > current.ncc;
  }
  return candidate.valid_pixels > current.valid_pixels;
}

py::dict matrix_candidate_to_dict(const MatrixCandidateMetrics& metrics, const char* model) {
  py::dict result;
  result["valid_pixels"] = metrics.valid_pixels;
  result["sampled_pixels"] = metrics.sampled_pixels;
  result["sample_stride"] = metrics.sample_stride;
  result["rms"] = metrics.rms;
  result["mean_abs_diff"] = metrics.mean_abs_diff;
  result["ncc"] = metrics.ncc;
  result["model"] = model;
  return result;
}

MatrixCandidateMetrics score_matrix_translation_candidates_f32_workspace(
    const float* d_reference,
    const float* d_moving,
    const std::array<float, 9>& base_matrix,
    const std::vector<std::pair<float, float>>& offsets,
    int width,
    int height,
    int sample_stride,
    MatrixRefineWorkspace workspace) {
  if (offsets.empty()) {
    throw std::invalid_argument("candidate offsets must be non-empty");
  }
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sampled_pixels = sample_width * sample_height;
  const int candidate_count = static_cast<int>(offsets.size());
  if (candidate_count > workspace.candidate_capacity ||
      workspace.d_inverses == nullptr ||
      workspace.d_partial_stats == nullptr ||
      workspace.d_partial_count == nullptr) {
    throw std::invalid_argument("matrix refine workspace is smaller than candidate count");
  }

  std::vector<std::array<float, 9>> matrices(offsets.size());
  std::vector<float> inverses(static_cast<std::size_t>(candidate_count) * 9, 0.0f);
  for (int i = 0; i < candidate_count; ++i) {
    auto matrix = base_matrix;
    matrix[2] += offsets[static_cast<std::size_t>(i)].first;
    matrix[5] += offsets[static_cast<std::size_t>(i)].second;
    matrices[static_cast<std::size_t>(i)] = matrix;
    const auto inverse = invert_matrix3x3(matrix);
    std::copy(inverse.begin(), inverse.end(), inverses.begin() + static_cast<std::size_t>(i) * 9);
  }

  std::vector<double> partial_stats(static_cast<std::size_t>(candidate_count) * 7, 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(candidate_count), 0ULL);
  check_cuda(
      cudaMemcpy(workspace.d_inverses, inverses.data(), inverses.size() * sizeof(float), cudaMemcpyHostToDevice),
      "cudaMemcpy(matrix refine candidate inverses)");
  glass_matrix_alignment_metrics_candidates_f32_launch(
      d_reference,
      d_moving,
      workspace.d_inverses,
      workspace.d_partial_stats,
      workspace.d_partial_count,
      width,
      height,
      stride,
      candidate_count);
  check_cuda(cudaGetLastError(), "matrix translation refine candidate kernel launch");
  check_cuda(cudaDeviceSynchronize(), "matrix translation refine candidate synchronize");
  check_cuda(
      cudaMemcpy(
          partial_stats.data(),
          workspace.d_partial_stats,
          partial_stats.size() * sizeof(double),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix refine partial stats)");
  check_cuda(
      cudaMemcpy(
          partial_count.data(),
          workspace.d_partial_count,
          partial_count.size() * sizeof(unsigned long long),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix refine partial count)");

  MatrixCandidateMetrics best;
  bool have_best = false;
  for (int i = 0; i < candidate_count; ++i) {
    const std::size_t offset = static_cast<std::size_t>(i) * 7;
    const auto metrics = metrics_from_sums(
        matrices[static_cast<std::size_t>(i)],
        offsets[static_cast<std::size_t>(i)].first,
        offsets[static_cast<std::size_t>(i)].second,
        partial_stats.data() + offset,
        partial_count[static_cast<std::size_t>(i)],
        sampled_pixels,
        stride);
    if (!have_best || better_matrix_metric(metrics, best)) {
      best = metrics;
      have_best = true;
    }
  }
  return best;
}

MatrixCandidateMetrics score_matrix_translation_candidates_f32(
    const float* d_reference,
    const float* d_moving,
    const std::array<float, 9>& base_matrix,
    const std::vector<std::pair<float, float>>& offsets,
    int width,
    int height,
    int sample_stride) {
  if (offsets.empty()) {
    throw std::invalid_argument("candidate offsets must be non-empty");
  }
  const int candidate_count = static_cast<int>(offsets.size());
  MatrixRefineWorkspace workspace;
  workspace.candidate_capacity = candidate_count;
  try {
    check_cuda(
        cudaMalloc(&workspace.d_inverses, static_cast<std::size_t>(candidate_count) * 9 * sizeof(float)),
        "cudaMalloc(matrix refine candidate inverses)");
    check_cuda(
        cudaMalloc(&workspace.d_partial_stats, static_cast<std::size_t>(candidate_count) * 7 * sizeof(double)),
        "cudaMalloc(matrix refine partial stats)");
    check_cuda(
        cudaMalloc(
            &workspace.d_partial_count,
            static_cast<std::size_t>(candidate_count) * sizeof(unsigned long long)),
        "cudaMalloc(matrix refine partial count)");
    const MatrixCandidateMetrics best = score_matrix_translation_candidates_f32_workspace(
        d_reference, d_moving, base_matrix, offsets, width, height, sample_stride, workspace);
    cudaFree(workspace.d_inverses);
    cudaFree(workspace.d_partial_stats);
    cudaFree(workspace.d_partial_count);
    return best;
  } catch (...) {
    cudaFree(workspace.d_inverses);
    cudaFree(workspace.d_partial_stats);
    cudaFree(workspace.d_partial_count);
    throw;
  }
}

std::vector<MatrixCandidateMetrics> score_matrix_translation_candidates_batch_f32_workspace(
    const float* d_reference,
    const float* d_stack,
    std::size_t pixels_per_frame,
    const std::vector<std::size_t>& moving_indices,
    const std::vector<std::array<float, 9>>& base_matrices,
    const std::vector<std::vector<std::pair<float, float>>>& offsets_by_frame,
    int width,
    int height,
    int sample_stride,
    MatrixRefineWorkspace workspace) {
  if (moving_indices.empty()) {
    return {};
  }
  if (base_matrices.size() != moving_indices.size() || offsets_by_frame.size() != moving_indices.size()) {
    throw std::invalid_argument("batch matrix scoring requires one matrix and offset list per moving frame");
  }
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sampled_pixels = sample_width * sample_height;

  std::vector<int> frame_starts(moving_indices.size(), 0);
  std::vector<int> frame_counts(moving_indices.size(), 0);
  std::size_t total_candidates_size = 0;
  for (std::size_t frame = 0; frame < moving_indices.size(); ++frame) {
    if (offsets_by_frame[frame].empty()) {
      throw std::invalid_argument("candidate offsets must be non-empty");
    }
    if (moving_indices[frame] > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("moving frame index exceeds native batch metric index range");
    }
    total_candidates_size += offsets_by_frame[frame].size();
  }
  if (total_candidates_size > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
    throw std::invalid_argument("too many matrix metric candidates for one native batch");
  }
  const int total_candidates = static_cast<int>(total_candidates_size);
  if (total_candidates > workspace.candidate_capacity ||
      workspace.d_inverses == nullptr ||
      workspace.d_partial_stats == nullptr ||
      workspace.d_partial_count == nullptr ||
      workspace.d_moving_frame_indices == nullptr) {
    throw std::invalid_argument("matrix batch refine workspace is smaller than candidate count");
  }

  std::vector<std::array<float, 9>> matrices(total_candidates_size);
  std::vector<std::pair<float, float>> candidate_offsets(total_candidates_size);
  std::vector<float> inverses(total_candidates_size * 9, 0.0f);
  std::vector<int> moving_frame_indices(total_candidates_size, 0);
  std::size_t cursor = 0;
  for (std::size_t frame = 0; frame < moving_indices.size(); ++frame) {
    frame_starts[frame] = static_cast<int>(cursor);
    frame_counts[frame] = static_cast<int>(offsets_by_frame[frame].size());
    const int moving_index = static_cast<int>(moving_indices[frame]);
    for (const auto& offset : offsets_by_frame[frame]) {
      auto matrix = base_matrices[frame];
      matrix[2] += offset.first;
      matrix[5] += offset.second;
      matrices[cursor] = matrix;
      candidate_offsets[cursor] = offset;
      moving_frame_indices[cursor] = moving_index;
      const auto inverse = invert_matrix3x3(matrix);
      std::copy(inverse.begin(), inverse.end(), inverses.begin() + cursor * 9);
      ++cursor;
    }
  }

  std::vector<double> partial_stats(total_candidates_size * 7, 0.0);
  std::vector<unsigned long long> partial_count(total_candidates_size, 0ULL);
  check_cuda(
      cudaMemcpy(workspace.d_inverses, inverses.data(), inverses.size() * sizeof(float), cudaMemcpyHostToDevice),
      "cudaMemcpy(matrix batch refine candidate inverses)");
  check_cuda(
      cudaMemcpy(
          workspace.d_moving_frame_indices,
          moving_frame_indices.data(),
          moving_frame_indices.size() * sizeof(int),
          cudaMemcpyHostToDevice),
      "cudaMemcpy(matrix batch refine moving frame indices)");
  glass_matrix_alignment_metrics_batch_candidates_f32_launch(
      d_reference,
      d_stack,
      workspace.d_moving_frame_indices,
      static_cast<unsigned long long>(pixels_per_frame),
      workspace.d_inverses,
      workspace.d_partial_stats,
      workspace.d_partial_count,
      width,
      height,
      stride,
      total_candidates);
  check_cuda(cudaGetLastError(), "matrix batch translation refine candidate kernel launch");
  check_cuda(cudaDeviceSynchronize(), "matrix batch translation refine candidate synchronize");
  check_cuda(
      cudaMemcpy(
          partial_stats.data(),
          workspace.d_partial_stats,
          partial_stats.size() * sizeof(double),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix batch refine partial stats)");
  check_cuda(
      cudaMemcpy(
          partial_count.data(),
          workspace.d_partial_count,
          partial_count.size() * sizeof(unsigned long long),
          cudaMemcpyDeviceToHost),
      "cudaMemcpy(matrix batch refine partial count)");

  std::vector<MatrixCandidateMetrics> results;
  results.reserve(moving_indices.size());
  for (std::size_t frame = 0; frame < moving_indices.size(); ++frame) {
    MatrixCandidateMetrics best;
    bool have_best = false;
    const int start = frame_starts[frame];
    const int count = frame_counts[frame];
    for (int local = 0; local < count; ++local) {
      const int candidate = start + local;
      const std::size_t candidate_offset = static_cast<std::size_t>(candidate) * 7;
      const auto metrics = metrics_from_sums(
          matrices[static_cast<std::size_t>(candidate)],
          candidate_offsets[static_cast<std::size_t>(candidate)].first,
          candidate_offsets[static_cast<std::size_t>(candidate)].second,
          partial_stats.data() + candidate_offset,
          partial_count[static_cast<std::size_t>(candidate)],
          sampled_pixels,
          stride);
      if (!have_best || better_matrix_metric(metrics, best)) {
        best = metrics;
        have_best = true;
      }
    }
    if (!have_best) {
      throw std::runtime_error("matrix batch refine produced no candidates");
    }
    results.push_back(best);
  }
  return results;
}

std::vector<MatrixCandidateMetrics> score_star_core_matrix_candidates_f32(
    const float* d_reference,
    const float* d_moving,
    const std::vector<std::array<float, 9>>& matrices,
    int width,
    int height,
    float threshold) {
  if (matrices.empty()) {
    throw std::invalid_argument("candidate matrices must be non-empty");
  }
  if (!std::isfinite(threshold)) {
    throw std::invalid_argument("star core threshold must be finite");
  }
  const int candidate_count = static_cast<int>(matrices.size());
  const int sampled_pixels = width * height;

  std::vector<float> inverses(static_cast<std::size_t>(candidate_count) * 9, 0.0f);
  for (int i = 0; i < candidate_count; ++i) {
    const auto inverse = invert_matrix3x3(matrices[static_cast<std::size_t>(i)]);
    std::copy(inverse.begin(), inverse.end(), inverses.begin() + static_cast<std::size_t>(i) * 9);
  }

  std::vector<double> partial_stats(static_cast<std::size_t>(candidate_count) * 7, 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(candidate_count), 0ULL);
  float* d_inverses = nullptr;
  double* d_partial_stats = nullptr;
  unsigned long long* d_partial_count = nullptr;
  try {
    check_cuda(
        cudaMalloc(&d_inverses, inverses.size() * sizeof(float)),
        "cudaMalloc(star core metric inverses)");
    check_cuda(
        cudaMalloc(&d_partial_stats, partial_stats.size() * sizeof(double)),
        "cudaMalloc(star core metric partial stats)");
    check_cuda(
        cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
        "cudaMalloc(star core metric partial count)");
    check_cuda(
        cudaMemcpy(d_inverses, inverses.data(), inverses.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(star core metric inverses)");
    glass_star_core_metrics_candidates_f32_launch(
        d_reference,
        d_moving,
        d_inverses,
        threshold,
        d_partial_stats,
        d_partial_count,
        width,
        height,
        candidate_count);
    check_cuda(cudaGetLastError(), "star core candidate metrics kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star core candidate metrics synchronize");
    check_cuda(
        cudaMemcpy(partial_stats.data(), d_partial_stats, partial_stats.size() * sizeof(double), cudaMemcpyDeviceToHost),
        "cudaMemcpy(star core metric partial stats)");
    check_cuda(
        cudaMemcpy(
            partial_count.data(),
            d_partial_count,
            partial_count.size() * sizeof(unsigned long long),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(star core metric partial count)");
  } catch (...) {
    cudaFree(d_inverses);
    cudaFree(d_partial_stats);
    cudaFree(d_partial_count);
    throw;
  }
  cudaFree(d_inverses);
  cudaFree(d_partial_stats);
  cudaFree(d_partial_count);

  std::vector<MatrixCandidateMetrics> results;
  results.reserve(matrices.size());
  for (int i = 0; i < candidate_count; ++i) {
    const std::size_t offset = static_cast<std::size_t>(i) * 7;
    results.push_back(metrics_from_sums(
        matrices[static_cast<std::size_t>(i)],
        0.0f,
        0.0f,
        partial_stats.data() + offset,
        partial_count[static_cast<std::size_t>(i)],
        sampled_pixels,
        1));
  }
  return results;
}

py::dict device_info_dict(int device_id) {
  cudaDeviceProp props{};
  check_cuda(cudaGetDeviceProperties(&props, device_id), "cudaGetDeviceProperties");
  py::dict info;
  info["device_id"] = device_id;
  info["name"] = std::string(props.name);
  info["compute_capability"] = std::to_string(props.major) + "." + std::to_string(props.minor);
  info["memory_total_mib"] = static_cast<unsigned long long>(props.totalGlobalMem / (1024 * 1024));
  info["multi_processor_count"] = props.multiProcessorCount;
  info["native_backend"] = true;
  info["available_to_glass"] = true;
  return info;
}

py::array_t<float> host_pinned_empty_f32(std::size_t height, std::size_t width) {
  if (height == 0 || width == 0) {
    throw std::invalid_argument("pinned host array dimensions must be non-empty");
  }
  float* ptr = nullptr;
  check_cuda(
      cudaHostAlloc(
          reinterpret_cast<void**>(&ptr),
          height * width * sizeof(float),
          cudaHostAllocPortable),
      "cudaHostAlloc(host_pinned_empty_f32)");
  py::capsule owner(ptr, [](void* value) {
    if (value != nullptr) {
      cudaFreeHost(value);
    }
  });
  return py::array_t<float>(
      {static_cast<py::ssize_t>(height), static_cast<py::ssize_t>(width)},
      {static_cast<py::ssize_t>(width * sizeof(float)), static_cast<py::ssize_t>(sizeof(float))},
      ptr,
      owner);
}

py::array_t<unsigned char> host_pinned_empty_u8(std::size_t byte_count) {
  if (byte_count == 0) {
    throw std::invalid_argument("pinned host byte array must be non-empty");
  }
  unsigned char* ptr = nullptr;
  check_cuda(
      cudaHostAlloc(
          reinterpret_cast<void**>(&ptr),
          byte_count,
          cudaHostAllocPortable),
      "cudaHostAlloc(host_pinned_empty_u8)");
  py::capsule owner(ptr, [](void* value) {
    if (value != nullptr) {
      cudaFreeHost(value);
    }
  });
  return py::array_t<unsigned char>(
      {static_cast<py::ssize_t>(byte_count)},
      {static_cast<py::ssize_t>(sizeof(unsigned char))},
      ptr,
      owner);
}

int bytes_per_fits_sample(int bitpix) {
  switch (bitpix) {
    case 8:
      return 1;
    case 16:
      return 2;
    case 32:
    case -32:
      return 4;
    case 64:
    case -64:
      return 8;
    default:
      throw std::invalid_argument("unsupported FITS BITPIX for native direct decode");
  }
}

std::uint16_t read_be_u16(const unsigned char* p) {
  return static_cast<std::uint16_t>((static_cast<std::uint16_t>(p[0]) << 8) |
                                    static_cast<std::uint16_t>(p[1]));
}

std::uint32_t read_be_u32(const unsigned char* p) {
  return (static_cast<std::uint32_t>(p[0]) << 24) |
         (static_cast<std::uint32_t>(p[1]) << 16) |
         (static_cast<std::uint32_t>(p[2]) << 8) |
         static_cast<std::uint32_t>(p[3]);
}

std::uint64_t read_be_u64(const unsigned char* p) {
  return (static_cast<std::uint64_t>(p[0]) << 56) |
         (static_cast<std::uint64_t>(p[1]) << 48) |
         (static_cast<std::uint64_t>(p[2]) << 40) |
         (static_cast<std::uint64_t>(p[3]) << 32) |
         (static_cast<std::uint64_t>(p[4]) << 24) |
         (static_cast<std::uint64_t>(p[5]) << 16) |
         (static_cast<std::uint64_t>(p[6]) << 8) |
         static_cast<std::uint64_t>(p[7]);
}

std::int16_t signed_from_u16_bits(std::uint16_t bits) {
  std::int16_t value = 0;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

std::int32_t signed_from_u32_bits(std::uint32_t bits) {
  std::int32_t value = 0;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

std::int64_t signed_from_u64_bits(std::uint64_t bits) {
  std::int64_t value = 0;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

float decode_fits_sample_f32(
    const unsigned char* p,
    int bitpix,
    double bscale,
    double bzero,
    bool has_blank,
    long long blank) {
  if (bitpix == 8) {
    const long long raw = static_cast<long long>(p[0]);
    if (has_blank && raw == blank) {
      return std::numeric_limits<float>::quiet_NaN();
    }
    return static_cast<float>(static_cast<double>(raw) * bscale + bzero);
  }
  if (bitpix == 16) {
    const auto raw = static_cast<long long>(signed_from_u16_bits(read_be_u16(p)));
    if (has_blank && raw == blank) {
      return std::numeric_limits<float>::quiet_NaN();
    }
    return static_cast<float>(static_cast<double>(raw) * bscale + bzero);
  }
  if (bitpix == 32) {
    const auto raw = static_cast<long long>(signed_from_u32_bits(read_be_u32(p)));
    if (has_blank && raw == blank) {
      return std::numeric_limits<float>::quiet_NaN();
    }
    return static_cast<float>(static_cast<double>(raw) * bscale + bzero);
  }
  if (bitpix == 64) {
    const auto raw = static_cast<long long>(signed_from_u64_bits(read_be_u64(p)));
    if (has_blank && raw == blank) {
      return std::numeric_limits<float>::quiet_NaN();
    }
    return static_cast<float>(static_cast<double>(raw) * bscale + bzero);
  }
  if (bitpix == -32) {
    const std::uint32_t bits = read_be_u32(p);
    float value = 0.0f;
    std::memcpy(&value, &bits, sizeof(float));
    return static_cast<float>(static_cast<double>(value) * bscale + bzero);
  }
  if (bitpix == -64) {
    const std::uint64_t bits = read_be_u64(p);
    double value = 0.0;
    std::memcpy(&value, &bits, sizeof(double));
    return static_cast<float>(value * bscale + bzero);
  }
  throw std::invalid_argument("unsupported FITS BITPIX for native direct decode");
}

void decode_fits_chunk_f32(
    const unsigned char* raw,
    float* out,
    std::size_t count,
    int bitpix,
    double bscale,
    double bzero,
    bool has_blank,
    long long blank) {
  if (bitpix == 16 && !has_blank && bscale == 1.0 && bzero == 32768.0) {
    for (std::size_t i = 0; i < count; ++i) {
      const std::uint16_t bits = read_be_u16(raw + i * 2u);
      out[i] = static_cast<float>(bits ^ 0x8000u);
    }
    return;
  }
  if (bitpix == 16) {
    for (std::size_t i = 0; i < count; ++i) {
      const std::uint16_t bits = read_be_u16(raw + i * 2u);
      const auto sample = static_cast<long long>(signed_from_u16_bits(bits));
      if (has_blank && sample == blank) {
        out[i] = std::numeric_limits<float>::quiet_NaN();
      } else {
        out[i] = static_cast<float>(static_cast<double>(sample) * bscale + bzero);
      }
    }
    return;
  }
  if (bitpix == -32 && !has_blank && bscale == 1.0 && bzero == 0.0) {
    for (std::size_t i = 0; i < count; ++i) {
      const std::uint32_t bits = read_be_u32(raw + i * 4u);
      float value = 0.0f;
      std::memcpy(&value, &bits, sizeof(float));
      out[i] = value;
    }
    return;
  }
  for (std::size_t i = 0; i < count; ++i) {
    out[i] = decode_fits_sample_f32(
        raw + i * static_cast<std::size_t>(bytes_per_fits_sample(bitpix)),
        bitpix,
        bscale,
        bzero,
        has_blank,
        blank);
  }
}

py::dict read_simple_fits_into_f32(
    const std::string& path,
    unsigned long long data_offset,
    std::size_t height,
    std::size_t width,
    int bitpix,
    double bscale,
    double bzero,
    py::object blank_obj,
    py::array_t<float, py::array::c_style> output) {
  if (height == 0 || width == 0) {
    throw std::invalid_argument("FITS output dimensions must be non-empty");
  }
  const py::buffer_info info = output.request();
  if (info.ndim != 2 ||
      static_cast<std::size_t>(info.shape[0]) != height ||
      static_cast<std::size_t>(info.shape[1]) != width) {
    throw std::invalid_argument("output shape does not match FITS image shape");
  }
  const bool has_blank = !blank_obj.is_none();
  const long long blank = has_blank ? py::cast<long long>(blank_obj) : 0LL;
  float* out = static_cast<float*>(info.ptr);
  const std::size_t pixel_count = height * width;
  const int bytes_per_sample = bytes_per_fits_sample(bitpix);
  constexpr std::size_t chunk_pixels = 1u << 20;
  std::vector<unsigned char> raw(chunk_pixels * static_cast<std::size_t>(bytes_per_sample));

  using Clock = std::chrono::steady_clock;
  const auto total_start = Clock::now();
  const auto open_start = Clock::now();
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    throw std::runtime_error("failed to open FITS image for native direct decode: " + path);
  }
  stream.seekg(static_cast<std::streamoff>(data_offset), std::ios::beg);
  if (!stream) {
    throw std::runtime_error("failed to seek FITS image data offset");
  }
  const auto open_stop = Clock::now();
  double read_s = 0.0;
  double decode_s = 0.0;
  unsigned long long bytes_read = 0;

  {
    py::gil_scoped_release release;
    std::size_t done = 0;
    while (done < pixel_count) {
      const std::size_t count = std::min(chunk_pixels, pixel_count - done);
      const std::size_t byte_count = count * static_cast<std::size_t>(bytes_per_sample);
      const auto read_start = Clock::now();
      stream.read(reinterpret_cast<char*>(raw.data()), static_cast<std::streamsize>(byte_count));
      const auto read_stop = Clock::now();
      if (stream.gcount() != static_cast<std::streamsize>(byte_count)) {
        throw std::runtime_error("truncated FITS image data during native direct decode");
      }
      read_s += std::chrono::duration<double>(read_stop - read_start).count();
      bytes_read += static_cast<unsigned long long>(byte_count);

      const auto decode_start = Clock::now();
      decode_fits_chunk_f32(raw.data(), out + done, count, bitpix, bscale, bzero, has_blank, blank);
      const auto decode_stop = Clock::now();
      decode_s += std::chrono::duration<double>(decode_stop - decode_start).count();
      done += count;
    }
  }

  const auto total_stop = Clock::now();
  py::dict result;
  result["schema_version"] = 1;
  result["backend"] = "native_direct_simple";
  result["bitpix"] = bitpix;
  result["height"] = static_cast<unsigned long long>(height);
  result["width"] = static_cast<unsigned long long>(width);
  result["bytes_read"] = bytes_read;
  result["file_open_s"] = std::chrono::duration<double>(open_stop - open_start).count();
  result["file_read_s"] = read_s;
  result["decode_s"] = decode_s;
  result["total_s"] = std::chrono::duration<double>(total_stop - total_start).count();
  result["applied_scale"] = (bscale != 1.0 || bzero != 0.0);
  result["applied_blank"] = has_blank;
  return result;
}

py::dict read_simple_fits_raw_into_u8(
    const std::string& path,
    unsigned long long data_offset,
    std::size_t byte_count,
    py::array_t<unsigned char, py::array::c_style> output) {
  if (byte_count == 0) {
    throw std::invalid_argument("FITS raw byte count must be non-empty");
  }
  const py::buffer_info info = output.request();
  if (info.ndim != 1 || static_cast<std::size_t>(info.shape[0]) != byte_count) {
    throw std::invalid_argument("raw output shape does not match FITS byte count");
  }
  auto* out = static_cast<unsigned char*>(info.ptr);

  using Clock = std::chrono::steady_clock;
  const auto total_start = Clock::now();
  const auto open_start = Clock::now();
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    throw std::runtime_error("failed to open FITS image for raw native read: " + path);
  }
  stream.seekg(static_cast<std::streamoff>(data_offset), std::ios::beg);
  if (!stream) {
    throw std::runtime_error("failed to seek FITS raw image data offset");
  }
  const auto open_stop = Clock::now();
  double read_s = 0.0;

  {
    py::gil_scoped_release release;
    constexpr std::size_t chunk_bytes = 8u << 20;
    std::size_t done = 0;
    while (done < byte_count) {
      const std::size_t count = std::min(chunk_bytes, byte_count - done);
      const auto read_start = Clock::now();
      stream.read(reinterpret_cast<char*>(out + done), static_cast<std::streamsize>(count));
      const auto read_stop = Clock::now();
      if (stream.gcount() != static_cast<std::streamsize>(count)) {
        throw std::runtime_error("truncated FITS image data during raw native read");
      }
      read_s += std::chrono::duration<double>(read_stop - read_start).count();
      done += count;
    }
  }

  const auto total_stop = Clock::now();
  py::dict result;
  result["schema_version"] = 1;
  result["backend"] = "native_u16be_raw";
  result["bytes_read"] = static_cast<unsigned long long>(byte_count);
  result["file_open_s"] = std::chrono::duration<double>(open_stop - open_start).count();
  result["file_read_s"] = read_s;
  result["decode_s"] = 0.0;
  result["total_s"] = std::chrono::duration<double>(total_stop - total_start).count();
  return result;
}

struct RawFitsReadTiming {
  double file_open_s = 0.0;
  double file_read_s = 0.0;
  double total_s = 0.0;
  unsigned long long bytes_read = 0;
  std::string backend = "std_ifstream";
};

#ifdef _WIN32
std::wstring utf8_to_wide_path(const std::string& path) {
  if (path.empty()) {
    return std::wstring();
  }
  const int required = MultiByteToWideChar(
      CP_UTF8,
      MB_ERR_INVALID_CHARS,
      path.data(),
      static_cast<int>(path.size()),
      nullptr,
      0);
  if (required <= 0) {
    throw std::runtime_error("failed to convert UTF-8 path for Win32 raw FITS read");
  }
  std::wstring wide(static_cast<std::size_t>(required), L'\0');
  const int written = MultiByteToWideChar(
      CP_UTF8,
      MB_ERR_INVALID_CHARS,
      path.data(),
      static_cast<int>(path.size()),
      wide.data(),
      required);
  if (written != required) {
    throw std::runtime_error("short UTF-8 path conversion for Win32 raw FITS read");
  }
  return wide;
}

std::string win32_error_message(const std::string& prefix, DWORD error) {
  std::ostringstream message;
  message << prefix << " (GetLastError=" << static_cast<unsigned long>(error) << ")";
  return message.str();
}

RawFitsReadTiming read_raw_fits_bytes_into_ptr_win32_sequential(
    const std::string& path,
    unsigned long long data_offset,
    std::size_t byte_count,
    unsigned char* out) {
  using Clock = std::chrono::steady_clock;
  const auto total_start = Clock::now();
  const auto open_start = Clock::now();
  const std::wstring wide_path = utf8_to_wide_path(path);
  HANDLE handle = CreateFileW(
      wide_path.c_str(),
      GENERIC_READ,
      FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
      nullptr,
      OPEN_EXISTING,
      FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN,
      nullptr);
  if (handle == INVALID_HANDLE_VALUE) {
    throw std::runtime_error(
        win32_error_message("failed to open FITS image for Win32 sequential raw read", GetLastError()) +
        ": " + path);
  }
  struct HandleCloser {
    HANDLE handle = INVALID_HANDLE_VALUE;
    ~HandleCloser() {
      if (handle != INVALID_HANDLE_VALUE) {
        CloseHandle(handle);
      }
    }
  } closer{handle};
  LARGE_INTEGER offset;
  offset.QuadPart = static_cast<LONGLONG>(data_offset);
  if (!SetFilePointerEx(handle, offset, nullptr, FILE_BEGIN)) {
    throw std::runtime_error(
        win32_error_message("failed to seek FITS raw image data offset", GetLastError()));
  }
  const auto open_stop = Clock::now();
  double read_s = 0.0;
  constexpr std::size_t chunk_bytes = 8u << 20;
  std::size_t done = 0;
  while (done < byte_count) {
    const std::size_t count = std::min(chunk_bytes, byte_count - done);
    const DWORD to_read = static_cast<DWORD>(count);
    DWORD bytes_read = 0;
    const auto read_start = Clock::now();
    const BOOL ok = ReadFile(handle, out + done, to_read, &bytes_read, nullptr);
    const auto read_stop = Clock::now();
    if (!ok) {
      throw std::runtime_error(
          win32_error_message("failed during Win32 sequential raw FITS read", GetLastError()));
    }
    if (bytes_read != to_read) {
      throw std::runtime_error("truncated FITS image data during Win32 sequential raw native read");
    }
    read_s += std::chrono::duration<double>(read_stop - read_start).count();
    done += count;
  }
  const auto total_stop = Clock::now();

  RawFitsReadTiming timing;
  timing.file_open_s = std::chrono::duration<double>(open_stop - open_start).count();
  timing.file_read_s = read_s;
  timing.total_s = std::chrono::duration<double>(total_stop - total_start).count();
  timing.bytes_read = static_cast<unsigned long long>(byte_count);
  timing.backend = "win32_sequential_scan";
  return timing;
}
#endif

RawFitsReadTiming read_raw_fits_bytes_into_ptr_ifstream(
    const std::string& path,
    unsigned long long data_offset,
    std::size_t byte_count,
    unsigned char* out) {
  using Clock = std::chrono::steady_clock;
  const auto total_start = Clock::now();
  const auto open_start = Clock::now();
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    throw std::runtime_error("failed to open FITS image for raw native batch read: " + path);
  }
  stream.seekg(static_cast<std::streamoff>(data_offset), std::ios::beg);
  if (!stream) {
    throw std::runtime_error("failed to seek FITS raw image data offset");
  }
  const auto open_stop = Clock::now();
  double read_s = 0.0;
  constexpr std::size_t chunk_bytes = 8u << 20;
  std::size_t done = 0;
  while (done < byte_count) {
    const std::size_t count = std::min(chunk_bytes, byte_count - done);
    const auto read_start = Clock::now();
    stream.read(reinterpret_cast<char*>(out + done), static_cast<std::streamsize>(count));
    const auto read_stop = Clock::now();
    if (stream.gcount() != static_cast<std::streamsize>(count)) {
      throw std::runtime_error("truncated FITS image data during raw native batch read");
    }
    read_s += std::chrono::duration<double>(read_stop - read_start).count();
    done += count;
  }
  const auto total_stop = Clock::now();

  RawFitsReadTiming timing;
  timing.file_open_s = std::chrono::duration<double>(open_stop - open_start).count();
  timing.file_read_s = read_s;
  timing.total_s = std::chrono::duration<double>(total_stop - total_start).count();
  timing.bytes_read = static_cast<unsigned long long>(byte_count);
  timing.backend = "std_ifstream";
  return timing;
}

RawFitsReadTiming read_raw_fits_bytes_into_ptr(
    const std::string& path,
    unsigned long long data_offset,
    std::size_t byte_count,
    unsigned char* out,
    const std::string& backend_policy) {
  if (backend_policy == "auto" || backend_policy == "std_ifstream") {
    return read_raw_fits_bytes_into_ptr_ifstream(path, data_offset, byte_count, out);
  }
  if (backend_policy == "win32_sequential_scan") {
#ifdef _WIN32
    return read_raw_fits_bytes_into_ptr_win32_sequential(path, data_offset, byte_count, out);
#else
    throw std::runtime_error("win32_sequential_scan raw FITS read backend is only available on Windows");
#endif
  }
  throw std::invalid_argument("unknown raw FITS read backend policy: " + backend_policy);
}

RawFitsReadTiming read_raw_fits_bytes_into_ptr(
    const std::string& path,
    unsigned long long data_offset,
    std::size_t byte_count,
    unsigned char* out) {
  return read_raw_fits_bytes_into_ptr(path, data_offset, byte_count, out, "auto");
}

py::dict read_simple_fits_raw_batch_into_u8(
    const std::vector<std::string>& paths,
    const std::vector<unsigned long long>& data_offsets,
    const std::vector<std::size_t>& byte_counts,
    py::sequence outputs,
    int max_workers) {
  const std::size_t frame_count = paths.size();
  if (frame_count == 0) {
    throw std::invalid_argument("native raw FITS batch requires at least one frame");
  }
  if (data_offsets.size() != frame_count || byte_counts.size() != frame_count) {
    throw std::invalid_argument("native raw FITS batch inputs must have matching lengths");
  }
  if (static_cast<std::size_t>(py::len(outputs)) != frame_count) {
    throw std::invalid_argument("native raw FITS batch output count must match input count");
  }

  struct BatchJob {
    std::string path;
    unsigned long long data_offset = 0;
    std::size_t byte_count = 0;
    unsigned char* out = nullptr;
    RawFitsReadTiming timing;
    std::string error;
  };

  std::vector<py::array_t<unsigned char, py::array::c_style>> output_refs;
  output_refs.reserve(frame_count);
  std::vector<BatchJob> jobs;
  jobs.reserve(frame_count);
  unsigned long long requested_bytes = 0;
  for (std::size_t index = 0; index < frame_count; ++index) {
    if (byte_counts[index] == 0) {
      throw std::invalid_argument("native raw FITS batch byte counts must be non-empty");
    }
    py::array_t<unsigned char, py::array::c_style> output =
        py::cast<py::array_t<unsigned char, py::array::c_style>>(outputs[index]);
    const py::buffer_info info = output.request();
    if (info.ndim != 1 || static_cast<std::size_t>(info.shape[0]) != byte_counts[index]) {
      throw std::invalid_argument("native raw FITS batch output shape does not match byte count");
    }
    output_refs.push_back(output);
    BatchJob job;
    job.path = paths[index];
    job.data_offset = data_offsets[index];
    job.byte_count = byte_counts[index];
    job.out = static_cast<unsigned char*>(info.ptr);
    requested_bytes += static_cast<unsigned long long>(byte_counts[index]);
    jobs.push_back(job);
  }

  const int requested_workers = max_workers <= 0 ? static_cast<int>(frame_count) : max_workers;
  const std::size_t worker_count = std::max<std::size_t>(
      1u,
      std::min<std::size_t>(static_cast<std::size_t>(requested_workers), frame_count));
  using Clock = std::chrono::steady_clock;
  const auto total_start = Clock::now();
  {
    py::gil_scoped_release release;
    std::atomic<std::size_t> next_job{0};
    std::vector<std::thread> threads;
    threads.reserve(worker_count);
    for (std::size_t worker = 0; worker < worker_count; ++worker) {
      threads.emplace_back([&jobs, &next_job, frame_count]() {
        for (;;) {
          const std::size_t index = next_job.fetch_add(1);
          if (index >= frame_count) {
            break;
          }
          try {
            jobs[index].timing = read_raw_fits_bytes_into_ptr(
                jobs[index].path,
                jobs[index].data_offset,
                jobs[index].byte_count,
                jobs[index].out);
          } catch (const std::exception& exc) {
            jobs[index].error = exc.what();
          } catch (...) {
            jobs[index].error = "unknown native raw FITS batch read error";
          }
        }
      });
    }
    for (auto& thread : threads) {
      thread.join();
    }
  }
  const auto total_stop = Clock::now();

  for (std::size_t index = 0; index < frame_count; ++index) {
    if (!jobs[index].error.empty()) {
      std::ostringstream message;
      message << "native raw FITS batch read failed for frame " << index
              << " (" << jobs[index].path << "): " << jobs[index].error;
      throw std::runtime_error(message.str());
    }
  }

  double open_s = 0.0;
  double read_s = 0.0;
  double cumulative_total_s = 0.0;
  unsigned long long bytes_read = 0;
  py::list per_frame;
  for (std::size_t index = 0; index < frame_count; ++index) {
    const RawFitsReadTiming& timing = jobs[index].timing;
    open_s += timing.file_open_s;
    read_s += timing.file_read_s;
    cumulative_total_s += timing.total_s;
    bytes_read += timing.bytes_read;
    py::dict item;
    item["index"] = static_cast<unsigned long long>(index);
    item["path"] = jobs[index].path;
    item["bytes_read"] = timing.bytes_read;
    item["file_open_s"] = timing.file_open_s;
    item["file_read_s"] = timing.file_read_s;
    item["decode_s"] = 0.0;
    item["total_s"] = timing.total_s;
    per_frame.append(item);
  }

  py::dict result;
  result["schema_version"] = 1;
  result["backend"] = "native_u16be_raw_batch";
  result["frame_count"] = static_cast<unsigned long long>(frame_count);
  result["worker_count"] = static_cast<unsigned long long>(worker_count);
  result["bytes_requested"] = requested_bytes;
  result["bytes_read"] = bytes_read;
  result["file_open_s"] = open_s;
  result["file_read_s"] = read_s;
  result["decode_s"] = 0.0;
  result["total_s"] = std::chrono::duration<double>(total_stop - total_start).count();
  result["cumulative_total_s"] = cumulative_total_s;
  result["per_frame"] = per_frame;
  return result;
}

class RawFitsReadQueue {
 public:
  explicit RawFitsReadQueue(int worker_count) {
    const int requested_workers = worker_count <= 0 ? 1 : worker_count;
    worker_count_ = std::max<std::size_t>(1u, static_cast<std::size_t>(requested_workers));
    workers_.reserve(worker_count_);
    for (std::size_t index = 0; index < worker_count_; ++index) {
      workers_.emplace_back([this]() { worker_loop(); });
    }
  }

  RawFitsReadQueue(const RawFitsReadQueue&) = delete;
  RawFitsReadQueue& operator=(const RawFitsReadQueue&) = delete;

  ~RawFitsReadQueue() {
    close();
  }

  py::dict submit(
      unsigned long long frame_index,
      const std::string& path,
      unsigned long long data_offset,
      std::size_t byte_count,
      py::array_t<unsigned char, py::array::c_style> output) {
    if (byte_count == 0) {
      throw std::invalid_argument("native raw FITS queue byte count must be non-empty");
    }
    const py::buffer_info info = output.request();
    if (info.ndim != 1 || static_cast<std::size_t>(info.shape[0]) != byte_count) {
      throw std::invalid_argument("native raw FITS queue output shape does not match byte count");
    }

    RawFitsReadJob job;
    job.frame_index = frame_index;
    job.path = path;
    job.data_offset = data_offset;
    job.byte_count = byte_count;
    job.out = static_cast<unsigned char*>(info.ptr);

    std::size_t pending_after = 0;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      if (closing_) {
        throw std::runtime_error("native raw FITS queue is closed");
      }
      requested_bytes_ += static_cast<unsigned long long>(byte_count);
      jobs_.push_back(std::move(job));
      ++submitted_count_;
      pending_after = jobs_.size() + active_count_;
    }
    job_condition_.notify_one();

    py::dict result;
    result["schema_version"] = 1;
    result["backend"] = "native_u16be_raw_queue";
    result["frame_index"] = frame_index;
    result["pending_count"] = static_cast<unsigned long long>(pending_after);
    result["submitted_count"] = static_cast<unsigned long long>(submitted_count_.load());
    result["worker_count"] = static_cast<unsigned long long>(worker_count_);
    return result;
  }

  py::object wait_completed(double timeout_s = -1.0) {
    RawFitsReadCompletion completion;
    bool has_completion = false;
    bool timed_out = false;
    {
      py::gil_scoped_release release;
      std::unique_lock<std::mutex> lock(mutex_);
      const auto ready = [this]() {
        return !completed_.empty() || (closing_ && jobs_.empty() && active_count_ == 0);
      };
      if (timeout_s < 0.0) {
        completed_condition_.wait(lock, ready);
      } else {
        const auto timeout = std::chrono::duration<double>(timeout_s);
        if (!completed_condition_.wait_for(lock, timeout, ready)) {
          timed_out = true;
        }
      }
      if (!timed_out && !completed_.empty()) {
        completion = std::move(completed_.front());
        completed_.pop_front();
        has_completion = true;
      }
    }

    if (timed_out) {
      return py::none();
    }
    if (!has_completion) {
      return py::none();
    }
    if (!completion.error.empty()) {
      std::ostringstream message;
      message << "native raw FITS queue read failed for frame "
              << completion.frame_index << " (" << completion.path
              << "): " << completion.error;
      throw std::runtime_error(message.str());
    }

    py::dict result;
    result["schema_version"] = 1;
    result["backend"] = "native_u16be_raw_queue";
    result["frame_index"] = completion.frame_index;
    result["path"] = completion.path;
    result["bytes_read"] = completion.timing.bytes_read;
    result["file_open_s"] = completion.timing.file_open_s;
    result["file_read_s"] = completion.timing.file_read_s;
    result["decode_s"] = 0.0;
    result["total_s"] = completion.timing.total_s;
    result["completed_count"] = static_cast<unsigned long long>(completed_count_.load());
    result["worker_count"] = static_cast<unsigned long long>(worker_count_);
    return result;
  }

  py::dict stats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    py::dict result;
    result["schema_version"] = 1;
    result["backend"] = "native_u16be_raw_queue";
    result["worker_count"] = static_cast<unsigned long long>(worker_count_);
    result["submitted_count"] = static_cast<unsigned long long>(submitted_count_.load());
    result["completed_count"] = static_cast<unsigned long long>(completed_count_.load());
    result["queued_count"] = static_cast<unsigned long long>(jobs_.size());
    result["active_count"] = static_cast<unsigned long long>(active_count_);
    result["ready_count"] = static_cast<unsigned long long>(completed_.size());
    result["requested_bytes"] = requested_bytes_;
    result["closed"] = closing_;
    return result;
  }

  void close() {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      if (closing_ && joined_) {
        return;
      }
      closing_ = true;
    }
    job_condition_.notify_all();
    completed_condition_.notify_all();
    for (auto& worker : workers_) {
      if (worker.joinable()) {
        worker.join();
      }
    }
    {
      std::lock_guard<std::mutex> lock(mutex_);
      joined_ = true;
    }
    completed_condition_.notify_all();
  }

 private:
  struct RawFitsReadJob {
    unsigned long long frame_index = 0;
    std::string path;
    unsigned long long data_offset = 0;
    std::size_t byte_count = 0;
    unsigned char* out = nullptr;
  };

  struct RawFitsReadCompletion {
    unsigned long long frame_index = 0;
    std::string path;
    RawFitsReadTiming timing;
    std::string error;
  };

  void worker_loop() {
    for (;;) {
      RawFitsReadJob job;
      {
        std::unique_lock<std::mutex> lock(mutex_);
        job_condition_.wait(lock, [this]() { return closing_ || !jobs_.empty(); });
        if (jobs_.empty()) {
          if (closing_) {
            break;
          }
          continue;
        }
        job = std::move(jobs_.front());
        jobs_.pop_front();
        ++active_count_;
      }

      RawFitsReadCompletion completion;
      completion.frame_index = job.frame_index;
      completion.path = job.path;
      try {
        completion.timing = read_raw_fits_bytes_into_ptr(
            job.path,
            job.data_offset,
            job.byte_count,
            job.out);
      } catch (const std::exception& exc) {
        completion.error = exc.what();
      } catch (...) {
        completion.error = "unknown native raw FITS queue read error";
      }

      {
        std::lock_guard<std::mutex> lock(mutex_);
        --active_count_;
        completed_.push_back(std::move(completion));
        ++completed_count_;
      }
      completed_condition_.notify_all();
    }
    completed_condition_.notify_all();
  }

  std::size_t worker_count_ = 1;
  mutable std::mutex mutex_;
  std::condition_variable job_condition_;
  std::condition_variable completed_condition_;
  std::deque<RawFitsReadJob> jobs_;
  std::deque<RawFitsReadCompletion> completed_;
  std::vector<std::thread> workers_;
  std::size_t active_count_ = 0;
  unsigned long long requested_bytes_ = 0;
  std::atomic<unsigned long long> submitted_count_{0};
  std::atomic<unsigned long long> completed_count_{0};
  bool closing_ = false;
  bool joined_ = false;
};

class ResidentCalibratedStack {
 public:
  ResidentCalibratedStack(std::size_t frame_count, std::size_t height, std::size_t width)
      : frame_count_(frame_count),
        height_(height),
        width_(width),
        pixels_per_frame_(height * width),
        loaded_(frame_count, 0) {
    if (frame_count_ == 0 || height_ == 0 || width_ == 0) {
      throw std::invalid_argument("resident stack dimensions must be non-empty");
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    check_cuda(cudaMalloc(&d_stack_, frame_count_ * frame_bytes), "cudaMalloc(resident calibrated stack)");
    check_cuda(cudaMalloc(&d_light_, frame_bytes), "cudaMalloc(resident raw light buffer)");
    check_cuda(cudaStreamCreate(&calibrate_stream_), "cudaStreamCreate(resident calibration stream)");
    check_cuda(cudaEventCreate(&calibrate_h2d_start_), "cudaEventCreate(resident reusable h2d start)");
    check_cuda(cudaEventCreate(&calibrate_h2d_stop_), "cudaEventCreate(resident reusable h2d stop)");
    check_cuda(cudaEventCreate(&calibrate_kernel_start_), "cudaEventCreate(resident reusable calibration start)");
    check_cuda(cudaEventCreate(&calibrate_kernel_stop_), "cudaEventCreate(resident reusable calibration stop)");
  }

  ResidentCalibratedStack(const ResidentCalibratedStack&) = delete;
  ResidentCalibratedStack& operator=(const ResidentCalibratedStack&) = delete;

  ~ResidentCalibratedStack() {
    if (calibrate_h2d_start_ != nullptr) {
      cudaEventDestroy(calibrate_h2d_start_);
    }
    if (calibrate_h2d_stop_ != nullptr) {
      cudaEventDestroy(calibrate_h2d_stop_);
    }
    if (calibrate_kernel_start_ != nullptr) {
      cudaEventDestroy(calibrate_kernel_start_);
    }
    if (calibrate_kernel_stop_ != nullptr) {
      cudaEventDestroy(calibrate_kernel_stop_);
    }
    if (calibrate_stream_ != nullptr) {
      cudaStreamDestroy(calibrate_stream_);
    }
    for (cudaEvent_t event : calibration_lane_start_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaEvent_t event : calibration_lane_stop_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaEvent_t event : calibration_lane_h2d_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaEvent_t event : calibration_lane_h2d_start_events_) {
      if (event != nullptr) {
        cudaEventDestroy(event);
      }
    }
    for (cudaStream_t stream : calibration_lane_streams_) {
      if (stream != nullptr) {
        cudaStreamDestroy(stream);
      }
    }
    if (h_pinned_light_ != nullptr) {
      cudaFreeHost(h_pinned_light_);
    }
    cudaFree(d_stack_);
    cudaFree(d_light_);
    for (float* buffer : d_calibration_lane_lights_) {
      cudaFree(buffer);
    }
    cudaFree(d_bias_);
    cudaFree(d_dark_);
    cudaFree(d_flat_);
    cudaFree(d_warp_coverage_);
    cudaFree(d_warp_output_);
    cudaFree(d_warp_frame_coverage_);
    cudaFree(d_warp_inverse_);
  }

  std::size_t frame_count() const { return frame_count_; }
  std::size_t height() const { return height_; }
  std::size_t width() const { return width_; }
  std::size_t pixels_per_frame() const { return pixels_per_frame_; }
  std::size_t loaded_count() const { return loaded_count_; }
  std::size_t host_pinned_bytes() const {
    return h_pinned_light_ == nullptr ? 0 : pixels_per_frame_ * sizeof(float);
  }
  std::size_t calibration_lane_count() const { return d_calibration_lane_lights_.size(); }
  std::size_t calibration_lane_buffer_bytes() const {
    return d_calibration_lane_lights_.size() * pixels_per_frame_ * sizeof(float);
  }

  std::size_t warp_scratch_bytes() const {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    std::size_t total = 0;
    if (d_warp_output_ != nullptr) {
      total += frame_bytes;
    }
    if (d_warp_frame_coverage_ != nullptr) {
      total += frame_bytes;
    }
    if (d_warp_inverse_ != nullptr) {
      total += 9 * sizeof(float);
    }
    return total;
  }

  std::string warp_copy_mode() const {
    return "default_stream_async_device_to_device";
  }

  std::size_t bytes_allocated() const {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    std::size_t total = frame_count_ * frame_bytes + frame_bytes + calibration_lane_buffer_bytes();
    if (has_bias_) {
      total += frame_bytes;
    }
    if (has_dark_) {
      total += frame_bytes;
    }
    if (has_flat_) {
      total += frame_bytes;
    }
    if (d_warp_coverage_ != nullptr) {
      total += frame_bytes;
    }
    total += warp_scratch_bytes();
    return total;
  }

  std::size_t warp_coverage_frame_count() const { return warp_coverage_frame_count_; }

  void reset_warp_coverage() {
    allocate_warp_coverage_if_needed();
    check_cuda(
        cudaMemset(d_warp_coverage_, 0, pixels_per_frame_ * sizeof(float)),
        "cudaMemset(resident warp coverage)");
    warp_coverage_frame_count_ = 0;
  }

  void accumulate_full_warp_coverage_frame() {
    allocate_warp_coverage_if_needed();
    glass_coverage_accumulate_full_f32_launch(d_warp_coverage_, pixels_per_frame_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.accumulate_full_warp_coverage_frame kernel launch");
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.accumulate_full_warp_coverage_frame synchronize");
    ++warp_coverage_frame_count_;
  }

  py::array_t<float> warp_coverage_map() const {
    py::array_t<float> result(
        {static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info info = result.request();
    auto* output = static_cast<float*>(info.ptr);
    if (d_warp_coverage_ == nullptr) {
      std::fill(output, output + pixels_per_frame_, 0.0f);
      return result;
    }
    check_cuda(
        cudaMemcpy(output, d_warp_coverage_, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(resident warp coverage map)");
    return result;
  }

  py::array_t<float> download_frame_tile(
      std::size_t index,
      std::size_t x0,
      std::size_t y0,
      std::size_t x1,
      std::size_t y1) const {
    require_loaded(index, "resident frame tile download");
    if (x0 >= x1 || y0 >= y1 || x1 > width_ || y1 > height_) {
      throw std::out_of_range("resident frame tile bounds are invalid");
    }
    const std::size_t tile_width = x1 - x0;
    const std::size_t tile_height = y1 - y0;
    py::array_t<float> result(
        {static_cast<py::ssize_t>(tile_height), static_cast<py::ssize_t>(tile_width)});
    const py::buffer_info info = result.request();
    auto* output = static_cast<float*>(info.ptr);
    const float* source = d_stack_ + index * pixels_per_frame_ + y0 * width_ + x0;
    check_cuda(
        cudaMemcpy2D(
            output,
            tile_width * sizeof(float),
            source,
            width_ * sizeof(float),
            tile_width * sizeof(float),
            tile_height,
            cudaMemcpyDeviceToHost),
        "cudaMemcpy2D(resident frame tile)");
    return result;
  }

  py::array_t<float> download_frames_tile(
      py::object indices_obj,
      std::size_t x0,
      std::size_t y0,
      std::size_t x1,
      std::size_t y1) const {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    if (indices.empty()) {
      throw std::invalid_argument("indices must contain at least one frame index");
    }
    if (x0 >= x1 || y0 >= y1 || x1 > width_ || y1 > height_) {
      throw std::out_of_range("resident frame tile bounds are invalid");
    }
    const std::size_t tile_width = x1 - x0;
    const std::size_t tile_height = y1 - y0;
    py::array_t<float> result(
        {static_cast<py::ssize_t>(indices.size()),
         static_cast<py::ssize_t>(tile_height),
         static_cast<py::ssize_t>(tile_width)});
    const py::buffer_info info = result.request();
    auto* output = static_cast<float*>(info.ptr);
    const std::size_t output_frame_stride = tile_width * tile_height;
    for (std::size_t output_index = 0; output_index < indices.size(); ++output_index) {
      const std::size_t frame_index = indices[output_index];
      require_loaded(frame_index, "resident frame batch tile download");
      const float* source = d_stack_ + frame_index * pixels_per_frame_ + y0 * width_ + x0;
      check_cuda(
          cudaMemcpy2D(
              output + output_index * output_frame_stride,
              tile_width * sizeof(float),
              source,
              width_ * sizeof(float),
              tile_width * sizeof(float),
              tile_height,
              cudaMemcpyDeviceToHost),
          "cudaMemcpy2D(resident frame batch tile)");
    }
    return result;
  }

  void set_calibration_masters(py::object bias_obj, py::object dark_obj, py::object flat_obj) {
    upload_optional_master(bias_obj, &d_bias_, &has_bias_, "bias");
    upload_optional_master(dark_obj, &d_dark_, &has_dark_, "dark");
    upload_optional_master(flat_obj, &d_flat_, &has_flat_, "flat");
  }

  void upload_calibrated_frame(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> frame) {
    require_index(index);
    const py::buffer_info info = frame.request();
    require_frame_shape(info, height_, width_);
    check_cuda(
        cudaMemcpy(
            d_stack_ + index * pixels_per_frame_,
            info.ptr,
            pixels_per_frame_ * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(resident calibrated frame)");
    mark_loaded(index);
  }

  py::dict apply_invalid_mask_frame(
      std::size_t index,
      py::array_t<unsigned char, py::array::c_style | py::array::forcecast> invalid_mask) {
    require_loaded(index, "resident source DQ mask application");
    const py::buffer_info info = invalid_mask.request();
    if (info.ndim == 1) {
      if (static_cast<std::size_t>(info.shape[0]) != pixels_per_frame_) {
        throw std::invalid_argument("invalid_mask must have length height*width");
      }
    } else if (info.ndim == 2) {
      require_frame_shape(info, height_, width_);
    } else {
      throw std::invalid_argument("invalid_mask must have shape (height, width) or (height*width,)");
    }

    const auto total_start = Clock::now();
    const auto* mask_ptr = static_cast<const unsigned char*>(info.ptr);
    std::vector<unsigned char> host_mask(mask_ptr, mask_ptr + pixels_per_frame_);
    std::size_t invalid_count = 0;
    for (const unsigned char value : host_mask) {
      if (value != 0) {
        ++invalid_count;
      }
    }

    unsigned char* d_mask = nullptr;
    double upload_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    if (invalid_count > 0) {
      try {
        check_cuda(cudaMalloc(&d_mask, pixels_per_frame_ * sizeof(unsigned char)), "cudaMalloc(resident invalid mask)");
        const auto upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(d_mask, host_mask.data(), pixels_per_frame_ * sizeof(unsigned char), cudaMemcpyHostToDevice),
            "cudaMemcpy(resident invalid mask)");
        upload_s = seconds_since(upload_start);

        const auto kernel_start = Clock::now();
        glass_apply_invalid_mask_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_mask,
            pixels_per_frame_);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_invalid_mask_frame kernel launch");
        kernel_s = seconds_since(kernel_start);
        const auto sync_start = Clock::now();
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_invalid_mask_frame synchronize");
        sync_s = seconds_since(sync_start);
      } catch (...) {
        cudaFree(d_mask);
        throw;
      }
      cudaFree(d_mask);
    }

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.apply_invalid_mask_frame";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["invalid_samples"] = static_cast<unsigned long long>(invalid_count);
    result["applied"] = invalid_count > 0;
    result["mask_upload_s"] = upload_s;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_cosmetic_threshold_mask_frame(
      std::size_t index,
      float low_threshold,
      float high_threshold) {
    require_loaded(index, "resident source DQ cosmetic threshold application");
    if (std::isnan(low_threshold) || std::isnan(high_threshold) || low_threshold > high_threshold) {
      throw std::invalid_argument("cosmetic thresholds must be finite-or-infinite values with low <= high");
    }

    const auto total_start = Clock::now();
    unsigned long long* d_counts = nullptr;
    std::array<unsigned long long, 3> host_counts{0ULL, 0ULL, 0ULL};
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    try {
      check_cuda(
          cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident cosmetic threshold counts)");
      check_cuda(
          cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
          "cudaMemset(resident cosmetic threshold counts)");

      const auto kernel_start = Clock::now();
      glass_apply_cosmetic_threshold_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          low_threshold,
          high_threshold,
          d_counts);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frame kernel launch");
      kernel_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frame synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              host_counts.data(),
              d_counts,
              host_counts.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident cosmetic threshold counts)");
      counts_download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_counts);
      throw;
    }
    cudaFree(d_counts);

    const unsigned long long hot_count = host_counts[0];
    const unsigned long long cold_count = host_counts[1];
    const unsigned long long nonfinite_count = host_counts[2];
    const unsigned long long cosmetic_count = hot_count + cold_count;
    const unsigned long long invalid_count = cosmetic_count + nonfinite_count;

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frame";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["low_threshold"] = low_threshold;
    result["high_threshold"] = high_threshold;
    result["hot_samples"] = hot_count;
    result["cold_samples"] = cold_count;
    result["nonfinite_samples"] = nonfinite_count;
    result["cosmetic_corrected_samples"] = cosmetic_count;
    result["invalid_samples"] = invalid_count;
    result["applied"] = invalid_count > 0;
    result["mask_upload_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["total_s"] = seconds_since(total_start);
    result["detector_execution"] = "cuda_threshold_apply";
    return result;
  }

  py::dict count_cosmetic_threshold_mask_frame(
      std::size_t index,
      float low_threshold,
      float high_threshold) const {
    require_loaded(index, "resident source DQ cosmetic threshold count");
    if (std::isnan(low_threshold) || std::isnan(high_threshold) || low_threshold > high_threshold) {
      throw std::invalid_argument("cosmetic thresholds must be finite-or-infinite values with low <= high");
    }

    const auto total_start = Clock::now();
    unsigned long long* d_counts = nullptr;
    std::array<unsigned long long, 3> host_counts{0ULL, 0ULL, 0ULL};
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    try {
      check_cuda(
          cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident cosmetic threshold count-only counts)");
      check_cuda(
          cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
          "cudaMemset(resident cosmetic threshold count-only counts)");

      const auto kernel_start = Clock::now();
      glass_count_cosmetic_threshold_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          low_threshold,
          high_threshold,
          d_counts);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame kernel launch");
      kernel_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              host_counts.data(),
              d_counts,
              host_counts.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident cosmetic threshold count-only counts)");
      counts_download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_counts);
      throw;
    }
    cudaFree(d_counts);

    const unsigned long long hot_count = host_counts[0];
    const unsigned long long cold_count = host_counts[1];
    const unsigned long long nonfinite_count = host_counts[2];
    const unsigned long long cosmetic_count = hot_count + cold_count;
    const unsigned long long invalid_count = cosmetic_count + nonfinite_count;

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["low_threshold"] = low_threshold;
    result["high_threshold"] = high_threshold;
    result["hot_samples"] = hot_count;
    result["cold_samples"] = cold_count;
    result["nonfinite_samples"] = nonfinite_count;
    result["cosmetic_corrected_samples"] = cosmetic_count;
    result["invalid_samples"] = invalid_count;
    result["applied"] = false;
    result["mask_upload_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["total_s"] = seconds_since(total_start);
    result["detector_execution"] = "cuda_threshold_count";
    return result;
  }

  void validate_isolated_cosmetic_thresholds(
      float low_threshold,
      float high_threshold,
      float median,
      float sigma) const {
    if (std::isnan(low_threshold) || std::isnan(high_threshold) || low_threshold > high_threshold) {
      throw std::invalid_argument("isolated cosmetic thresholds must be finite-or-infinite values with low <= high");
    }
    if (!std::isfinite(median) || std::isnan(sigma) || sigma < 0.0f) {
      throw std::invalid_argument("isolated cosmetic median must be finite and sigma must be non-negative");
    }
  }

  py::dict isolated_cosmetic_result_dict(
      const std::array<unsigned long long, 7>& counts,
      const char* native_method,
      std::size_t index,
      float low_threshold,
      float high_threshold,
      float median,
      float sigma,
      float structure_sigma,
      int min_neighbor_support,
      bool applied_mode) const {
    const unsigned long long hot_count = counts[0];
    const unsigned long long cold_count = counts[1];
    const unsigned long long nonfinite_count = counts[2];
    const unsigned long long candidate_hot_count = counts[3];
    const unsigned long long candidate_cold_count = counts[4];
    const unsigned long long protected_hot_count = counts[5];
    const unsigned long long protected_cold_count = counts[6];
    const unsigned long long cosmetic_count = hot_count + cold_count;
    const unsigned long long invalid_count = cosmetic_count + nonfinite_count;

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = native_method;
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["low_threshold"] = low_threshold;
    result["high_threshold"] = high_threshold;
    result["median"] = median;
    result["sigma"] = sigma;
    result["structure_sigma"] = structure_sigma;
    result["min_neighbor_support"] = min_neighbor_support;
    result["hot_samples"] = hot_count;
    result["cold_samples"] = cold_count;
    result["nonfinite_samples"] = nonfinite_count;
    result["candidate_hot_samples"] = candidate_hot_count;
    result["candidate_cold_samples"] = candidate_cold_count;
    result["protected_hot_samples"] = protected_hot_count;
    result["protected_cold_samples"] = protected_cold_count;
    result["cosmetic_corrected_samples"] = cosmetic_count;
    result["invalid_samples"] = invalid_count;
    result["applied"] = applied_mode && invalid_count > 0ULL;
    return result;
  }

  py::dict star_protected_isolated_cosmetic_result_dict(
      const std::array<unsigned long long, 10>& counts,
      const char* native_method,
      std::size_t index,
      float low_threshold,
      float high_threshold,
      float median,
      float sigma,
      float structure_sigma,
      int min_neighbor_support,
      std::size_t star_count,
      float star_protection_radius,
      bool applied_mode) const {
    const unsigned long long hot_count = counts[0];
    const unsigned long long cold_count = counts[1];
    const unsigned long long nonfinite_count = counts[2];
    const unsigned long long candidate_hot_count = counts[3];
    const unsigned long long candidate_cold_count = counts[4];
    const unsigned long long protected_hot_count = counts[5];
    const unsigned long long protected_cold_count = counts[6];
    const unsigned long long star_protected_hot_count = counts[7];
    const unsigned long long star_protected_cold_count = counts[8];
    const unsigned long long star_protected_cosmetic_count = counts[9];
    const unsigned long long cosmetic_count = hot_count + cold_count;
    const unsigned long long invalid_count = cosmetic_count + nonfinite_count;

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = native_method;
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["low_threshold"] = low_threshold;
    result["high_threshold"] = high_threshold;
    result["median"] = median;
    result["sigma"] = sigma;
    result["structure_sigma"] = structure_sigma;
    result["min_neighbor_support"] = min_neighbor_support;
    result["star_count"] = static_cast<unsigned long long>(star_count);
    result["star_protection_radius_px"] = star_protection_radius;
    result["hot_samples"] = hot_count;
    result["cold_samples"] = cold_count;
    result["nonfinite_samples"] = nonfinite_count;
    result["candidate_hot_samples"] = candidate_hot_count;
    result["candidate_cold_samples"] = candidate_cold_count;
    result["protected_hot_samples"] = protected_hot_count;
    result["protected_cold_samples"] = protected_cold_count;
    result["star_protected_hot_samples"] = star_protected_hot_count;
    result["star_protected_cold_samples"] = star_protected_cold_count;
    result["star_protected_cosmetic_samples"] = star_protected_cosmetic_count;
    result["cosmetic_corrected_samples"] = cosmetic_count;
    result["invalid_samples"] = invalid_count;
    result["applied"] = applied_mode && invalid_count > 0ULL;
    result["star_catalog_source"] = "host_catalog_coordinates_device_applied";
    return result;
  }

  void validate_star_catalog_payload(
      const py::buffer_info& xs_info,
      const py::buffer_info& ys_info,
      float star_protection_radius) const {
    if (xs_info.ndim != 1 || ys_info.ndim != 1) {
      throw std::invalid_argument("star_xs and star_ys must be one-dimensional arrays");
    }
    if (xs_info.shape[0] != ys_info.shape[0]) {
      throw std::invalid_argument("star_xs and star_ys must have the same length");
    }
    if (xs_info.shape[0] > 8192) {
      throw std::invalid_argument("star-protected cosmetic threshold supports at most 8192 stars");
    }
    if (!std::isfinite(star_protection_radius) || star_protection_radius < 0.0f) {
      throw std::invalid_argument("star_protection_radius must be finite and non-negative");
    }
  }

  py::dict apply_isolated_cosmetic_threshold_mask_frame(
      std::size_t index,
      float low_threshold,
      float high_threshold,
      float median,
      float sigma,
      float structure_sigma,
      int min_neighbor_support) {
    require_loaded(index, "resident isolated source DQ cosmetic threshold application");
    validate_isolated_cosmetic_thresholds(low_threshold, high_threshold, median, sigma);

    const auto total_start = Clock::now();
    unsigned long long* d_counts = nullptr;
    std::array<unsigned long long, 7> host_counts{0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL};
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    try {
      check_cuda(
          cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident isolated cosmetic threshold counts)");
      check_cuda(
          cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
          "cudaMemset(resident isolated cosmetic threshold counts)");

      const auto kernel_start = Clock::now();
      glass_apply_isolated_cosmetic_threshold_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          width_,
          height_,
          low_threshold,
          high_threshold,
          median,
          sigma,
          structure_sigma,
          min_neighbor_support,
          d_counts);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame kernel launch");
      kernel_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              host_counts.data(),
              d_counts,
              host_counts.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident isolated cosmetic threshold counts)");
      counts_download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_counts);
      throw;
    }
    cudaFree(d_counts);

    py::dict result = isolated_cosmetic_result_dict(
        host_counts,
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame",
        index,
        low_threshold,
        high_threshold,
        median,
        sigma,
        structure_sigma,
        min_neighbor_support,
        true);
    result["mask_upload_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["total_s"] = seconds_since(total_start);
    result["detector_execution"] = "cuda_isolated_threshold_apply";
    return result;
  }

  py::dict count_isolated_cosmetic_threshold_mask_frame(
      std::size_t index,
      float low_threshold,
      float high_threshold,
      float median,
      float sigma,
      float structure_sigma,
      int min_neighbor_support) const {
    require_loaded(index, "resident isolated source DQ cosmetic threshold count");
    validate_isolated_cosmetic_thresholds(low_threshold, high_threshold, median, sigma);

    const auto total_start = Clock::now();
    unsigned long long* d_counts = nullptr;
    std::array<unsigned long long, 7> host_counts{0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL};
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    try {
      check_cuda(
          cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident isolated cosmetic threshold count-only counts)");
      check_cuda(
          cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
          "cudaMemset(resident isolated cosmetic threshold count-only counts)");

      const auto kernel_start = Clock::now();
      glass_count_isolated_cosmetic_threshold_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          width_,
          height_,
          low_threshold,
          high_threshold,
          median,
          sigma,
          structure_sigma,
          min_neighbor_support,
          d_counts);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame kernel launch");
      kernel_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              host_counts.data(),
              d_counts,
              host_counts.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident isolated cosmetic threshold count-only counts)");
      counts_download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_counts);
      throw;
    }
    cudaFree(d_counts);

    py::dict result = isolated_cosmetic_result_dict(
        host_counts,
        "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame",
        index,
        low_threshold,
        high_threshold,
        median,
        sigma,
        structure_sigma,
        min_neighbor_support,
        false);
    result["mask_upload_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["total_s"] = seconds_since(total_start);
    result["detector_execution"] = "cuda_isolated_threshold_count";
    return result;
  }

  py::dict apply_star_protected_isolated_cosmetic_threshold_mask_frame(
      std::size_t index,
      float low_threshold,
      float high_threshold,
      float median,
      float sigma,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_xs,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_ys,
      float star_protection_radius,
      float structure_sigma,
      int min_neighbor_support) {
    require_loaded(index, "resident star-protected isolated source DQ cosmetic threshold application");
    validate_isolated_cosmetic_thresholds(low_threshold, high_threshold, median, sigma);
    const py::buffer_info xs_info = star_xs.request();
    const py::buffer_info ys_info = star_ys.request();
    validate_star_catalog_payload(xs_info, ys_info, star_protection_radius);

    const auto total_start = Clock::now();
    const std::size_t star_count = static_cast<std::size_t>(xs_info.shape[0]);
    float* d_star_xs = nullptr;
    float* d_star_ys = nullptr;
    unsigned long long* d_counts = nullptr;
    std::array<unsigned long long, 10> host_counts{
        0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL};
    double catalog_upload_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    try {
      if (star_count > 0 && star_protection_radius > 0.0f) {
        check_cuda(
            cudaMalloc(&d_star_xs, star_count * sizeof(float)),
            "cudaMalloc(resident star-protected cosmetic star xs)");
        check_cuda(
            cudaMalloc(&d_star_ys, star_count * sizeof(float)),
            "cudaMalloc(resident star-protected cosmetic star ys)");
        const auto upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(d_star_xs, xs_info.ptr, star_count * sizeof(float), cudaMemcpyHostToDevice),
            "cudaMemcpy(resident star-protected cosmetic star xs)");
        check_cuda(
            cudaMemcpy(d_star_ys, ys_info.ptr, star_count * sizeof(float), cudaMemcpyHostToDevice),
            "cudaMemcpy(resident star-protected cosmetic star ys)");
        catalog_upload_s = seconds_since(upload_start);
      }
      check_cuda(
          cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident star-protected cosmetic threshold counts)");
      check_cuda(
          cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
          "cudaMemset(resident star-protected cosmetic threshold counts)");

      const auto kernel_start = Clock::now();
      glass_apply_star_protected_isolated_cosmetic_threshold_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          width_,
          height_,
          low_threshold,
          high_threshold,
          median,
          sigma,
          structure_sigma,
          min_neighbor_support,
          d_star_xs,
          d_star_ys,
          static_cast<int>(star_count),
          star_protection_radius,
          d_counts);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame kernel launch");
      kernel_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              host_counts.data(),
              d_counts,
              host_counts.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident star-protected cosmetic threshold counts)");
      counts_download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_star_xs);
      cudaFree(d_star_ys);
      cudaFree(d_counts);
      throw;
    }
    cudaFree(d_star_xs);
    cudaFree(d_star_ys);
    cudaFree(d_counts);

    py::dict result = star_protected_isolated_cosmetic_result_dict(
        host_counts,
        "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame",
        index,
        low_threshold,
        high_threshold,
        median,
        sigma,
        structure_sigma,
        min_neighbor_support,
        star_count,
        star_protection_radius,
        true);
    result["mask_upload_s"] = 0.0;
    result["star_catalog_upload_s"] = catalog_upload_s;
    result["star_catalog_upload_bytes"] = static_cast<unsigned long long>(star_count * sizeof(float) * 2ULL);
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["total_s"] = seconds_since(total_start);
    result["detector_execution"] = "cuda_star_catalog_protected_isolated_threshold_apply";
    return result;
  }

  py::dict count_star_protected_isolated_cosmetic_threshold_mask_frame(
      std::size_t index,
      float low_threshold,
      float high_threshold,
      float median,
      float sigma,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_xs,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_ys,
      float star_protection_radius,
      float structure_sigma,
      int min_neighbor_support) const {
    require_loaded(index, "resident star-protected isolated source DQ cosmetic threshold count");
    validate_isolated_cosmetic_thresholds(low_threshold, high_threshold, median, sigma);
    const py::buffer_info xs_info = star_xs.request();
    const py::buffer_info ys_info = star_ys.request();
    validate_star_catalog_payload(xs_info, ys_info, star_protection_radius);

    const auto total_start = Clock::now();
    const std::size_t star_count = static_cast<std::size_t>(xs_info.shape[0]);
    float* d_star_xs = nullptr;
    float* d_star_ys = nullptr;
    unsigned long long* d_counts = nullptr;
    std::array<unsigned long long, 10> host_counts{
        0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL};
    double catalog_upload_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    try {
      if (star_count > 0 && star_protection_radius > 0.0f) {
        check_cuda(
            cudaMalloc(&d_star_xs, star_count * sizeof(float)),
            "cudaMalloc(resident star-protected cosmetic count star xs)");
        check_cuda(
            cudaMalloc(&d_star_ys, star_count * sizeof(float)),
            "cudaMalloc(resident star-protected cosmetic count star ys)");
        const auto upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(d_star_xs, xs_info.ptr, star_count * sizeof(float), cudaMemcpyHostToDevice),
            "cudaMemcpy(resident star-protected cosmetic count star xs)");
        check_cuda(
            cudaMemcpy(d_star_ys, ys_info.ptr, star_count * sizeof(float), cudaMemcpyHostToDevice),
            "cudaMemcpy(resident star-protected cosmetic count star ys)");
        catalog_upload_s = seconds_since(upload_start);
      }
      check_cuda(
          cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident star-protected cosmetic threshold count counts)");
      check_cuda(
          cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
          "cudaMemset(resident star-protected cosmetic threshold count counts)");

      const auto kernel_start = Clock::now();
      glass_count_star_protected_isolated_cosmetic_threshold_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          width_,
          height_,
          low_threshold,
          high_threshold,
          median,
          sigma,
          structure_sigma,
          min_neighbor_support,
          d_star_xs,
          d_star_ys,
          static_cast<int>(star_count),
          star_protection_radius,
          d_counts);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frame kernel launch");
      kernel_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frame synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              host_counts.data(),
              d_counts,
              host_counts.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident star-protected cosmetic threshold count counts)");
      counts_download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_star_xs);
      cudaFree(d_star_ys);
      cudaFree(d_counts);
      throw;
    }
    cudaFree(d_star_xs);
    cudaFree(d_star_ys);
    cudaFree(d_counts);

    py::dict result = star_protected_isolated_cosmetic_result_dict(
        host_counts,
        "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frame",
        index,
        low_threshold,
        high_threshold,
        median,
        sigma,
        structure_sigma,
        min_neighbor_support,
        star_count,
        star_protection_radius,
        false);
    result["mask_upload_s"] = 0.0;
    result["star_catalog_upload_s"] = catalog_upload_s;
    result["star_catalog_upload_bytes"] = static_cast<unsigned long long>(star_count * sizeof(float) * 2ULL);
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["total_s"] = seconds_since(total_start);
    result["detector_execution"] = "cuda_star_catalog_protected_isolated_threshold_count";
    return result;
  }

  py::dict star_protected_isolated_cosmetic_threshold_mask_frames_impl(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj,
      py::iterable medians_obj,
      py::iterable sigmas_obj,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_xs_flat,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_ys_flat,
      py::iterable star_offsets_obj,
      py::iterable star_counts_obj,
      py::iterable star_protection_radii_obj,
      float structure_sigma,
      int min_neighbor_support,
      bool applied_mode) {
    std::vector<unsigned long long> frame_indices;
    std::vector<float> low_thresholds;
    std::vector<float> high_thresholds;
    std::vector<float> medians;
    std::vector<float> sigmas;
    std::vector<unsigned long long> star_offsets;
    std::vector<unsigned long long> star_counts;
    std::vector<float> star_protection_radii;
    for (py::handle item : indices_obj) {
      const auto index = py::cast<std::size_t>(item);
      require_loaded(
          index,
          applied_mode
              ? "resident source DQ batch star-protected cosmetic threshold application"
              : "resident source DQ batch star-protected cosmetic threshold count");
      frame_indices.push_back(static_cast<unsigned long long>(index));
    }
    for (py::handle item : low_thresholds_obj) {
      low_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : high_thresholds_obj) {
      high_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : medians_obj) {
      medians.push_back(py::cast<float>(item));
    }
    for (py::handle item : sigmas_obj) {
      sigmas.push_back(py::cast<float>(item));
    }
    for (py::handle item : star_offsets_obj) {
      star_offsets.push_back(py::cast<unsigned long long>(item));
    }
    for (py::handle item : star_counts_obj) {
      star_counts.push_back(py::cast<unsigned long long>(item));
    }
    for (py::handle item : star_protection_radii_obj) {
      star_protection_radii.push_back(py::cast<float>(item));
    }
    validate_isolated_batch_payload(frame_indices, low_thresholds, high_thresholds, medians, sigmas);
    if (frame_indices.size() != star_offsets.size() ||
        frame_indices.size() != star_counts.size() ||
        frame_indices.size() != star_protection_radii.size()) {
      throw std::invalid_argument(
          "indices, star_offsets, star_counts, and star_protection_radii must have the same length");
    }
    const py::buffer_info xs_info = star_xs_flat.request();
    const py::buffer_info ys_info = star_ys_flat.request();
    if (xs_info.ndim != 1 || ys_info.ndim != 1) {
      throw std::invalid_argument("flattened star_xs and star_ys must be one-dimensional arrays");
    }
    if (xs_info.shape[0] != ys_info.shape[0]) {
      throw std::invalid_argument("flattened star_xs and star_ys must have the same length");
    }
    const std::size_t total_stars = static_cast<std::size_t>(xs_info.shape[0]);
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      if (star_counts[i] > 8192ULL) {
        throw std::invalid_argument("star-protected batch cosmetic threshold supports at most 8192 stars per frame");
      }
      if (!std::isfinite(star_protection_radii[i]) || star_protection_radii[i] < 0.0f) {
        throw std::invalid_argument("star_protection_radii must be finite and non-negative");
      }
      const std::size_t offset = static_cast<std::size_t>(star_offsets[i]);
      const std::size_t count = static_cast<std::size_t>(star_counts[i]);
      if (offset > total_stars || count > total_stars - offset) {
        throw std::invalid_argument("star_offsets/star_counts must stay within flattened star arrays");
      }
    }

    const auto total_start = Clock::now();
    unsigned long long* d_indices = nullptr;
    float* d_low_thresholds = nullptr;
    float* d_high_thresholds = nullptr;
    float* d_medians = nullptr;
    float* d_sigmas = nullptr;
    unsigned long long* d_star_offsets = nullptr;
    unsigned long long* d_star_counts = nullptr;
    float* d_star_xs = nullptr;
    float* d_star_ys = nullptr;
    float* d_star_protection_radii = nullptr;
    unsigned long long* d_counts = nullptr;
    std::vector<unsigned long long> host_counts(frame_indices.size() * 10ULL, 0ULL);
    double threshold_upload_s = 0.0;
    double star_catalog_upload_s = 0.0;
    double memset_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    const unsigned long long star_catalog_upload_bytes =
        static_cast<unsigned long long>(
            total_stars * sizeof(float) * 2ULL
            + star_offsets.size() * sizeof(unsigned long long)
            + star_counts.size() * sizeof(unsigned long long)
            + star_protection_radii.size() * sizeof(float));
    if (!frame_indices.empty()) {
      try {
        allocate_isolated_batch_buffers(
            frame_indices,
            low_thresholds,
            high_thresholds,
            medians,
            sigmas,
            &d_indices,
            &d_low_thresholds,
            &d_high_thresholds,
            &d_medians,
            &d_sigmas,
            &d_counts,
            threshold_upload_s,
            memset_s,
            host_counts.size(),
            applied_mode ? "star-protected application" : "star-protected count");
        check_cuda(
            cudaMalloc(&d_star_offsets, star_offsets.size() * sizeof(unsigned long long)),
            "cudaMalloc(resident batch star-protected star offsets)");
        check_cuda(
            cudaMalloc(&d_star_counts, star_counts.size() * sizeof(unsigned long long)),
            "cudaMalloc(resident batch star-protected star counts)");
        check_cuda(
            cudaMalloc(&d_star_protection_radii, star_protection_radii.size() * sizeof(float)),
            "cudaMalloc(resident batch star-protected radii)");
        if (total_stars > 0) {
          check_cuda(
              cudaMalloc(&d_star_xs, total_stars * sizeof(float)),
              "cudaMalloc(resident batch star-protected star xs)");
          check_cuda(
              cudaMalloc(&d_star_ys, total_stars * sizeof(float)),
              "cudaMalloc(resident batch star-protected star ys)");
        }

        const auto catalog_upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                d_star_offsets,
                star_offsets.data(),
                star_offsets.size() * sizeof(unsigned long long),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch star-protected star offsets)");
        check_cuda(
            cudaMemcpy(
                d_star_counts,
                star_counts.data(),
                star_counts.size() * sizeof(unsigned long long),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch star-protected star counts)");
        check_cuda(
            cudaMemcpy(
                d_star_protection_radii,
                star_protection_radii.data(),
                star_protection_radii.size() * sizeof(float),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch star-protected radii)");
        if (total_stars > 0) {
          check_cuda(
              cudaMemcpy(d_star_xs, xs_info.ptr, total_stars * sizeof(float), cudaMemcpyHostToDevice),
              "cudaMemcpy(resident batch star-protected star xs)");
          check_cuda(
              cudaMemcpy(d_star_ys, ys_info.ptr, total_stars * sizeof(float), cudaMemcpyHostToDevice),
              "cudaMemcpy(resident batch star-protected star ys)");
        }
        star_catalog_upload_s = seconds_since(catalog_upload_start);

        const auto kernel_start = Clock::now();
        if (applied_mode) {
          glass_apply_star_protected_isolated_cosmetic_threshold_mask_frames_f32_launch(
              d_stack_,
              width_,
              height_,
              d_indices,
              d_low_thresholds,
              d_high_thresholds,
              d_medians,
              d_sigmas,
              d_star_offsets,
              d_star_counts,
              d_star_xs,
              d_star_ys,
              d_star_protection_radii,
              frame_indices.size(),
              structure_sigma,
              min_neighbor_support,
              d_counts);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frames kernel launch");
        } else {
          glass_count_star_protected_isolated_cosmetic_threshold_mask_frames_f32_launch(
              d_stack_,
              width_,
              height_,
              d_indices,
              d_low_thresholds,
              d_high_thresholds,
              d_medians,
              d_sigmas,
              d_star_offsets,
              d_star_counts,
              d_star_xs,
              d_star_ys,
              d_star_protection_radii,
              frame_indices.size(),
              structure_sigma,
              min_neighbor_support,
              d_counts);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frames kernel launch");
        }
        kernel_s = seconds_since(kernel_start);
        const auto sync_start = Clock::now();
        check_cuda(
            cudaDeviceSynchronize(),
            applied_mode
                ? "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frames synchronize"
                : "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frames synchronize");
        sync_s = seconds_since(sync_start);
        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                host_counts.data(),
                d_counts,
                host_counts.size() * sizeof(unsigned long long),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch star-protected cosmetic threshold counts)");
        counts_download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_indices);
        cudaFree(d_low_thresholds);
        cudaFree(d_high_thresholds);
        cudaFree(d_medians);
        cudaFree(d_sigmas);
        cudaFree(d_star_offsets);
        cudaFree(d_star_counts);
        cudaFree(d_star_xs);
        cudaFree(d_star_ys);
        cudaFree(d_star_protection_radii);
        cudaFree(d_counts);
        throw;
      }
    }
    cudaFree(d_indices);
    cudaFree(d_low_thresholds);
    cudaFree(d_high_thresholds);
    cudaFree(d_medians);
    cudaFree(d_sigmas);
    cudaFree(d_star_offsets);
    cudaFree(d_star_counts);
    cudaFree(d_star_xs);
    cudaFree(d_star_ys);
    cudaFree(d_star_protection_radii);
    cudaFree(d_counts);

    return star_protected_isolated_cosmetic_batch_result_dict(
        host_counts,
        frame_indices,
        low_thresholds,
        high_thresholds,
        medians,
        sigmas,
        star_counts,
        star_protection_radii,
        structure_sigma,
        min_neighbor_support,
        applied_mode
            ? "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frames"
            : "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frames",
        applied_mode
            ? "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame"
            : "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frame",
        applied_mode
            ? "cuda_star_catalog_protected_isolated_threshold_apply_batch"
            : "cuda_star_catalog_protected_isolated_threshold_count_batch",
        applied_mode,
        threshold_upload_s,
        star_catalog_upload_s,
        star_catalog_upload_bytes,
        memset_s,
        kernel_s,
        sync_s,
        counts_download_s,
        seconds_since(total_start));
  }

  py::dict apply_star_protected_isolated_cosmetic_threshold_mask_frames(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj,
      py::iterable medians_obj,
      py::iterable sigmas_obj,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_xs_flat,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_ys_flat,
      py::iterable star_offsets_obj,
      py::iterable star_counts_obj,
      py::iterable star_protection_radii_obj,
      float structure_sigma,
      int min_neighbor_support) {
    return star_protected_isolated_cosmetic_threshold_mask_frames_impl(
        indices_obj,
        low_thresholds_obj,
        high_thresholds_obj,
        medians_obj,
        sigmas_obj,
        star_xs_flat,
        star_ys_flat,
        star_offsets_obj,
        star_counts_obj,
        star_protection_radii_obj,
        structure_sigma,
        min_neighbor_support,
        true);
  }

  py::dict count_star_protected_isolated_cosmetic_threshold_mask_frames(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj,
      py::iterable medians_obj,
      py::iterable sigmas_obj,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_xs_flat,
      py::array_t<float, py::array::c_style | py::array::forcecast> star_ys_flat,
      py::iterable star_offsets_obj,
      py::iterable star_counts_obj,
      py::iterable star_protection_radii_obj,
      float structure_sigma,
      int min_neighbor_support) {
    return star_protected_isolated_cosmetic_threshold_mask_frames_impl(
        indices_obj,
        low_thresholds_obj,
        high_thresholds_obj,
        medians_obj,
        sigmas_obj,
        star_xs_flat,
        star_ys_flat,
        star_offsets_obj,
        star_counts_obj,
        star_protection_radii_obj,
        structure_sigma,
        min_neighbor_support,
        false);
  }

  py::dict apply_cosmetic_threshold_mask_frames(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj) {
    std::vector<unsigned long long> frame_indices;
    std::vector<float> low_thresholds;
    std::vector<float> high_thresholds;
    for (py::handle item : indices_obj) {
      const auto index = py::cast<std::size_t>(item);
      require_loaded(index, "resident source DQ batch cosmetic threshold application");
      frame_indices.push_back(static_cast<unsigned long long>(index));
    }
    for (py::handle item : low_thresholds_obj) {
      low_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : high_thresholds_obj) {
      high_thresholds.push_back(py::cast<float>(item));
    }
    if (frame_indices.size() != low_thresholds.size() || frame_indices.size() != high_thresholds.size()) {
      throw std::invalid_argument("indices, low_thresholds, and high_thresholds must have the same length");
    }
    if (frame_indices.size() > 65535ULL) {
      throw std::invalid_argument("batch cosmetic threshold application supports at most 65535 frames per launch");
    }
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      if (std::isnan(low_thresholds[i]) || std::isnan(high_thresholds[i]) ||
          low_thresholds[i] > high_thresholds[i]) {
        throw std::invalid_argument("cosmetic thresholds must be finite-or-infinite values with low <= high");
      }
    }

    const auto total_start = Clock::now();
    unsigned long long* d_indices = nullptr;
    float* d_low_thresholds = nullptr;
    float* d_high_thresholds = nullptr;
    unsigned long long* d_counts = nullptr;
    std::vector<unsigned long long> host_counts(frame_indices.size() * 3ULL, 0ULL);
    double upload_s = 0.0;
    double memset_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    if (!frame_indices.empty()) {
      try {
        check_cuda(
            cudaMalloc(&d_indices, frame_indices.size() * sizeof(unsigned long long)),
            "cudaMalloc(resident batch cosmetic threshold indices)");
        check_cuda(
            cudaMalloc(&d_low_thresholds, low_thresholds.size() * sizeof(float)),
            "cudaMalloc(resident batch cosmetic low thresholds)");
        check_cuda(
            cudaMalloc(&d_high_thresholds, high_thresholds.size() * sizeof(float)),
            "cudaMalloc(resident batch cosmetic high thresholds)");
        check_cuda(
            cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
            "cudaMalloc(resident batch cosmetic threshold counts)");

        const auto upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                d_indices,
                frame_indices.data(),
                frame_indices.size() * sizeof(unsigned long long),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch cosmetic threshold indices)");
        check_cuda(
            cudaMemcpy(
                d_low_thresholds,
                low_thresholds.data(),
                low_thresholds.size() * sizeof(float),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch cosmetic low thresholds)");
        check_cuda(
            cudaMemcpy(
                d_high_thresholds,
                high_thresholds.data(),
                high_thresholds.size() * sizeof(float),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch cosmetic high thresholds)");
        upload_s = seconds_since(upload_start);

        const auto memset_start = Clock::now();
        check_cuda(
            cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
            "cudaMemset(resident batch cosmetic threshold counts)");
        memset_s = seconds_since(memset_start);

        const auto kernel_start = Clock::now();
        glass_apply_cosmetic_threshold_mask_frames_f32_launch(
            d_stack_,
            pixels_per_frame_,
            d_indices,
            d_low_thresholds,
            d_high_thresholds,
            frame_indices.size(),
            d_counts);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frames kernel launch");
        kernel_s = seconds_since(kernel_start);

        const auto sync_start = Clock::now();
        check_cuda(
            cudaDeviceSynchronize(),
            "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frames synchronize");
        sync_s = seconds_since(sync_start);

        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                host_counts.data(),
                d_counts,
                host_counts.size() * sizeof(unsigned long long),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch cosmetic threshold counts)");
        counts_download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_indices);
        cudaFree(d_low_thresholds);
        cudaFree(d_high_thresholds);
        cudaFree(d_counts);
        throw;
      }
    }
    cudaFree(d_indices);
    cudaFree(d_low_thresholds);
    cudaFree(d_high_thresholds);
    cudaFree(d_counts);

    py::list frames;
    unsigned long long total_hot = 0ULL;
    unsigned long long total_cold = 0ULL;
    unsigned long long total_nonfinite = 0ULL;
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      const unsigned long long hot_count = host_counts[i * 3ULL + 0ULL];
      const unsigned long long cold_count = host_counts[i * 3ULL + 1ULL];
      const unsigned long long nonfinite_count = host_counts[i * 3ULL + 2ULL];
      const unsigned long long cosmetic_count = hot_count + cold_count;
      const unsigned long long invalid_count = cosmetic_count + nonfinite_count;
      total_hot += hot_count;
      total_cold += cold_count;
      total_nonfinite += nonfinite_count;
      py::dict frame_result;
      frame_result["schema_version"] = 1;
      frame_result["native_method"] = "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frames";
      frame_result["per_frame_native_method"] = "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frame";
      frame_result["frame_index"] = frame_indices[i];
      frame_result["batch_position"] = static_cast<unsigned long long>(i);
      frame_result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
      frame_result["low_threshold"] = low_thresholds[i];
      frame_result["high_threshold"] = high_thresholds[i];
      frame_result["hot_samples"] = hot_count;
      frame_result["cold_samples"] = cold_count;
      frame_result["nonfinite_samples"] = nonfinite_count;
      frame_result["cosmetic_corrected_samples"] = cosmetic_count;
      frame_result["invalid_samples"] = invalid_count;
      frame_result["applied"] = invalid_count > 0;
      frame_result["mask_upload_s"] = 0.0;
      frame_result["threshold_upload_s"] = upload_s;
      frame_result["counts_memset_s"] = memset_s;
      frame_result["kernel_enqueue_s"] = kernel_s;
      frame_result["sync_s"] = sync_s;
      frame_result["device_counts_download_s"] = counts_download_s;
      frame_result["batch_single_kernel_launch"] = true;
      frame_result["batch_single_sync"] = true;
      frame_result["batch_frame_count"] = static_cast<unsigned long long>(frame_indices.size());
      frame_result["total_s"] = seconds_since(total_start);
      frame_result["detector_execution"] = "cuda_threshold_apply_batch";
      frames.append(frame_result);
    }

    const unsigned long long total_cosmetic = total_hot + total_cold;
    const unsigned long long total_invalid = total_cosmetic + total_nonfinite;
    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.apply_cosmetic_threshold_mask_frames";
    result["frame_count"] = static_cast<unsigned long long>(frame_indices.size());
    result["total_pixels_per_frame"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["hot_samples"] = total_hot;
    result["cold_samples"] = total_cold;
    result["nonfinite_samples"] = total_nonfinite;
    result["cosmetic_corrected_samples"] = total_cosmetic;
    result["invalid_samples"] = total_invalid;
    result["applied"] = total_invalid > 0ULL;
    result["mask_upload_s"] = 0.0;
    result["threshold_upload_s"] = upload_s;
    result["counts_memset_s"] = memset_s;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["batch_single_kernel_launch"] = true;
    result["batch_single_sync"] = true;
    result["detector_execution"] = "cuda_threshold_apply_batch";
    result["total_s"] = seconds_since(total_start);
    result["frames"] = frames;
    return result;
  }

  py::dict count_cosmetic_threshold_mask_frames(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj) const {
    std::vector<unsigned long long> frame_indices;
    std::vector<float> low_thresholds;
    std::vector<float> high_thresholds;
    for (py::handle item : indices_obj) {
      const auto index = py::cast<std::size_t>(item);
      require_loaded(index, "resident source DQ batch cosmetic threshold count");
      frame_indices.push_back(static_cast<unsigned long long>(index));
    }
    for (py::handle item : low_thresholds_obj) {
      low_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : high_thresholds_obj) {
      high_thresholds.push_back(py::cast<float>(item));
    }
    if (frame_indices.size() != low_thresholds.size() || frame_indices.size() != high_thresholds.size()) {
      throw std::invalid_argument("indices, low_thresholds, and high_thresholds must have the same length");
    }
    if (frame_indices.size() > 65535ULL) {
      throw std::invalid_argument("batch cosmetic threshold count supports at most 65535 frames per launch");
    }
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      if (std::isnan(low_thresholds[i]) || std::isnan(high_thresholds[i]) ||
          low_thresholds[i] > high_thresholds[i]) {
        throw std::invalid_argument("cosmetic thresholds must be finite-or-infinite values with low <= high");
      }
    }

    const auto total_start = Clock::now();
    unsigned long long* d_indices = nullptr;
    float* d_low_thresholds = nullptr;
    float* d_high_thresholds = nullptr;
    unsigned long long* d_counts = nullptr;
    std::vector<unsigned long long> host_counts(frame_indices.size() * 3ULL, 0ULL);
    double upload_s = 0.0;
    double memset_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    if (!frame_indices.empty()) {
      try {
        check_cuda(
            cudaMalloc(&d_indices, frame_indices.size() * sizeof(unsigned long long)),
            "cudaMalloc(resident batch cosmetic threshold count indices)");
        check_cuda(
            cudaMalloc(&d_low_thresholds, low_thresholds.size() * sizeof(float)),
            "cudaMalloc(resident batch cosmetic count low thresholds)");
        check_cuda(
            cudaMalloc(&d_high_thresholds, high_thresholds.size() * sizeof(float)),
            "cudaMalloc(resident batch cosmetic count high thresholds)");
        check_cuda(
            cudaMalloc(&d_counts, host_counts.size() * sizeof(unsigned long long)),
            "cudaMalloc(resident batch cosmetic threshold count counts)");

        const auto upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                d_indices,
                frame_indices.data(),
                frame_indices.size() * sizeof(unsigned long long),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch cosmetic threshold count indices)");
        check_cuda(
            cudaMemcpy(
                d_low_thresholds,
                low_thresholds.data(),
                low_thresholds.size() * sizeof(float),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch cosmetic count low thresholds)");
        check_cuda(
            cudaMemcpy(
                d_high_thresholds,
                high_thresholds.data(),
                high_thresholds.size() * sizeof(float),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch cosmetic count high thresholds)");
        upload_s = seconds_since(upload_start);

        const auto memset_start = Clock::now();
        check_cuda(
            cudaMemset(d_counts, 0, host_counts.size() * sizeof(unsigned long long)),
            "cudaMemset(resident batch cosmetic threshold count counts)");
        memset_s = seconds_since(memset_start);

        const auto kernel_start = Clock::now();
        glass_count_cosmetic_threshold_mask_frames_f32_launch(
            d_stack_,
            pixels_per_frame_,
            d_indices,
            d_low_thresholds,
            d_high_thresholds,
            frame_indices.size(),
            d_counts);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.count_cosmetic_threshold_mask_frames kernel launch");
        kernel_s = seconds_since(kernel_start);

        const auto sync_start = Clock::now();
        check_cuda(
            cudaDeviceSynchronize(),
            "ResidentCalibratedStack.count_cosmetic_threshold_mask_frames synchronize");
        sync_s = seconds_since(sync_start);

        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                host_counts.data(),
                d_counts,
                host_counts.size() * sizeof(unsigned long long),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch cosmetic threshold count counts)");
        counts_download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_indices);
        cudaFree(d_low_thresholds);
        cudaFree(d_high_thresholds);
        cudaFree(d_counts);
        throw;
      }
    }
    cudaFree(d_indices);
    cudaFree(d_low_thresholds);
    cudaFree(d_high_thresholds);
    cudaFree(d_counts);

    py::list frames;
    unsigned long long total_hot = 0ULL;
    unsigned long long total_cold = 0ULL;
    unsigned long long total_nonfinite = 0ULL;
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      const unsigned long long hot_count = host_counts[i * 3ULL + 0ULL];
      const unsigned long long cold_count = host_counts[i * 3ULL + 1ULL];
      const unsigned long long nonfinite_count = host_counts[i * 3ULL + 2ULL];
      const unsigned long long cosmetic_count = hot_count + cold_count;
      const unsigned long long invalid_count = cosmetic_count + nonfinite_count;
      total_hot += hot_count;
      total_cold += cold_count;
      total_nonfinite += nonfinite_count;
      py::dict frame_result;
      frame_result["schema_version"] = 1;
      frame_result["native_method"] = "ResidentCalibratedStack.count_cosmetic_threshold_mask_frames";
      frame_result["per_frame_native_method"] = "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame";
      frame_result["frame_index"] = frame_indices[i];
      frame_result["batch_position"] = static_cast<unsigned long long>(i);
      frame_result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
      frame_result["low_threshold"] = low_thresholds[i];
      frame_result["high_threshold"] = high_thresholds[i];
      frame_result["hot_samples"] = hot_count;
      frame_result["cold_samples"] = cold_count;
      frame_result["nonfinite_samples"] = nonfinite_count;
      frame_result["cosmetic_corrected_samples"] = cosmetic_count;
      frame_result["invalid_samples"] = invalid_count;
      frame_result["applied"] = false;
      frame_result["mask_upload_s"] = 0.0;
      frame_result["threshold_upload_s"] = upload_s;
      frame_result["counts_memset_s"] = memset_s;
      frame_result["kernel_enqueue_s"] = kernel_s;
      frame_result["sync_s"] = sync_s;
      frame_result["device_counts_download_s"] = counts_download_s;
      frame_result["batch_single_kernel_launch"] = true;
      frame_result["batch_single_sync"] = true;
      frame_result["batch_frame_count"] = static_cast<unsigned long long>(frame_indices.size());
      frame_result["total_s"] = seconds_since(total_start);
      frame_result["detector_execution"] = "cuda_threshold_count_batch";
      frames.append(frame_result);
    }

    const unsigned long long total_cosmetic = total_hot + total_cold;
    const unsigned long long total_invalid = total_cosmetic + total_nonfinite;
    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.count_cosmetic_threshold_mask_frames";
    result["frame_count"] = static_cast<unsigned long long>(frame_indices.size());
    result["total_pixels_per_frame"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["hot_samples"] = total_hot;
    result["cold_samples"] = total_cold;
    result["nonfinite_samples"] = total_nonfinite;
    result["cosmetic_corrected_samples"] = total_cosmetic;
    result["invalid_samples"] = total_invalid;
    result["applied"] = false;
    result["mask_upload_s"] = 0.0;
    result["threshold_upload_s"] = upload_s;
    result["counts_memset_s"] = memset_s;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["batch_single_kernel_launch"] = true;
    result["batch_single_sync"] = true;
    result["detector_execution"] = "cuda_threshold_count_batch";
    result["total_s"] = seconds_since(total_start);
    result["frames"] = frames;
    return result;
  }

  void validate_isolated_batch_payload(
      const std::vector<unsigned long long>& frame_indices,
      const std::vector<float>& low_thresholds,
      const std::vector<float>& high_thresholds,
      const std::vector<float>& medians,
      const std::vector<float>& sigmas) const {
    if (frame_indices.size() != low_thresholds.size() ||
        frame_indices.size() != high_thresholds.size() ||
        frame_indices.size() != medians.size() ||
        frame_indices.size() != sigmas.size()) {
      throw std::invalid_argument("indices, thresholds, medians, and sigmas must have the same length");
    }
    if (frame_indices.size() > 65535ULL) {
      throw std::invalid_argument("batch isolated cosmetic threshold processing supports at most 65535 frames per launch");
    }
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      validate_isolated_cosmetic_thresholds(low_thresholds[i], high_thresholds[i], medians[i], sigmas[i]);
    }
  }

  void allocate_isolated_batch_buffers(
      const std::vector<unsigned long long>& frame_indices,
      const std::vector<float>& low_thresholds,
      const std::vector<float>& high_thresholds,
      const std::vector<float>& medians,
      const std::vector<float>& sigmas,
      unsigned long long** d_indices,
      float** d_low_thresholds,
      float** d_high_thresholds,
      float** d_medians,
      float** d_sigmas,
      unsigned long long** d_counts,
      double& upload_s,
      double& memset_s,
      std::size_t count_slots,
      const char* label) const {
    (void)label;
    check_cuda(
        cudaMalloc(d_indices, frame_indices.size() * sizeof(unsigned long long)),
        "cudaMalloc(resident batch isolated cosmetic indices)");
    check_cuda(
        cudaMalloc(d_low_thresholds, low_thresholds.size() * sizeof(float)),
        "cudaMalloc(resident batch isolated cosmetic low thresholds)");
    check_cuda(
        cudaMalloc(d_high_thresholds, high_thresholds.size() * sizeof(float)),
        "cudaMalloc(resident batch isolated cosmetic high thresholds)");
    check_cuda(
        cudaMalloc(d_medians, medians.size() * sizeof(float)),
        "cudaMalloc(resident batch isolated cosmetic medians)");
    check_cuda(
        cudaMalloc(d_sigmas, sigmas.size() * sizeof(float)),
        "cudaMalloc(resident batch isolated cosmetic sigmas)");
    check_cuda(
        cudaMalloc(d_counts, count_slots * sizeof(unsigned long long)),
        "cudaMalloc(resident batch isolated cosmetic counts)");

    const auto upload_start = Clock::now();
    check_cuda(
        cudaMemcpy(*d_indices, frame_indices.data(), frame_indices.size() * sizeof(unsigned long long), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident batch isolated cosmetic indices)");
    check_cuda(
        cudaMemcpy(*d_low_thresholds, low_thresholds.data(), low_thresholds.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident batch isolated cosmetic low thresholds)");
    check_cuda(
        cudaMemcpy(*d_high_thresholds, high_thresholds.data(), high_thresholds.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident batch isolated cosmetic high thresholds)");
    check_cuda(
        cudaMemcpy(*d_medians, medians.data(), medians.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident batch isolated cosmetic medians)");
    check_cuda(
        cudaMemcpy(*d_sigmas, sigmas.data(), sigmas.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident batch isolated cosmetic sigmas)");
    upload_s = seconds_since(upload_start);

    const auto memset_start = Clock::now();
    check_cuda(
        cudaMemset(*d_counts, 0, count_slots * sizeof(unsigned long long)),
        "cudaMemset(resident batch isolated cosmetic counts)");
    memset_s = seconds_since(memset_start);
  }

  py::dict isolated_cosmetic_batch_result_dict(
      const std::vector<unsigned long long>& host_counts,
      const std::vector<unsigned long long>& frame_indices,
      const std::vector<float>& low_thresholds,
      const std::vector<float>& high_thresholds,
      const std::vector<float>& medians,
      const std::vector<float>& sigmas,
      float structure_sigma,
      int min_neighbor_support,
      const char* native_method,
      const char* per_frame_native_method,
      const char* detector_execution,
      bool applied_mode,
      double upload_s,
      double memset_s,
      double kernel_s,
      double sync_s,
      double counts_download_s,
      double total_s) const {
    py::list frames;
    unsigned long long total_hot = 0ULL;
    unsigned long long total_cold = 0ULL;
    unsigned long long total_nonfinite = 0ULL;
    unsigned long long total_candidate_hot = 0ULL;
    unsigned long long total_candidate_cold = 0ULL;
    unsigned long long total_protected_hot = 0ULL;
    unsigned long long total_protected_cold = 0ULL;
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      std::array<unsigned long long, 7> counts{
          host_counts[i * 7ULL + 0ULL],
          host_counts[i * 7ULL + 1ULL],
          host_counts[i * 7ULL + 2ULL],
          host_counts[i * 7ULL + 3ULL],
          host_counts[i * 7ULL + 4ULL],
          host_counts[i * 7ULL + 5ULL],
          host_counts[i * 7ULL + 6ULL]};
      total_hot += counts[0];
      total_cold += counts[1];
      total_nonfinite += counts[2];
      total_candidate_hot += counts[3];
      total_candidate_cold += counts[4];
      total_protected_hot += counts[5];
      total_protected_cold += counts[6];
      py::dict frame_result = isolated_cosmetic_result_dict(
          counts,
          native_method,
          static_cast<std::size_t>(frame_indices[i]),
          low_thresholds[i],
          high_thresholds[i],
          medians[i],
          sigmas[i],
          structure_sigma,
          min_neighbor_support,
          applied_mode);
      frame_result["per_frame_native_method"] = per_frame_native_method;
      frame_result["batch_position"] = static_cast<unsigned long long>(i);
      frame_result["mask_upload_s"] = 0.0;
      frame_result["threshold_upload_s"] = upload_s;
      frame_result["counts_memset_s"] = memset_s;
      frame_result["kernel_enqueue_s"] = kernel_s;
      frame_result["sync_s"] = sync_s;
      frame_result["device_counts_download_s"] = counts_download_s;
      frame_result["batch_single_kernel_launch"] = true;
      frame_result["batch_single_sync"] = true;
      frame_result["batch_frame_count"] = static_cast<unsigned long long>(frame_indices.size());
      frame_result["total_s"] = total_s;
      frame_result["detector_execution"] = detector_execution;
      frames.append(frame_result);
    }

    const unsigned long long total_cosmetic = total_hot + total_cold;
    const unsigned long long total_invalid = total_cosmetic + total_nonfinite;
    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = native_method;
    result["frame_count"] = static_cast<unsigned long long>(frame_indices.size());
    result["total_pixels_per_frame"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["hot_samples"] = total_hot;
    result["cold_samples"] = total_cold;
    result["nonfinite_samples"] = total_nonfinite;
    result["candidate_hot_samples"] = total_candidate_hot;
    result["candidate_cold_samples"] = total_candidate_cold;
    result["protected_hot_samples"] = total_protected_hot;
    result["protected_cold_samples"] = total_protected_cold;
    result["cosmetic_corrected_samples"] = total_cosmetic;
    result["invalid_samples"] = total_invalid;
    result["applied"] = applied_mode && total_invalid > 0ULL;
    result["mask_upload_s"] = 0.0;
    result["threshold_upload_s"] = upload_s;
    result["counts_memset_s"] = memset_s;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["batch_single_kernel_launch"] = true;
    result["batch_single_sync"] = true;
    result["detector_execution"] = detector_execution;
    result["total_s"] = total_s;
    result["structure_sigma"] = structure_sigma;
    result["min_neighbor_support"] = min_neighbor_support;
    result["frames"] = frames;
    return result;
  }

  py::dict star_protected_isolated_cosmetic_batch_result_dict(
      const std::vector<unsigned long long>& host_counts,
      const std::vector<unsigned long long>& frame_indices,
      const std::vector<float>& low_thresholds,
      const std::vector<float>& high_thresholds,
      const std::vector<float>& medians,
      const std::vector<float>& sigmas,
      const std::vector<unsigned long long>& star_counts,
      const std::vector<float>& star_protection_radii,
      float structure_sigma,
      int min_neighbor_support,
      const char* native_method,
      const char* per_frame_native_method,
      const char* detector_execution,
      bool applied_mode,
      double threshold_upload_s,
      double star_catalog_upload_s,
      unsigned long long star_catalog_upload_bytes,
      double memset_s,
      double kernel_s,
      double sync_s,
      double counts_download_s,
      double total_s) const {
    py::list frames;
    unsigned long long total_hot = 0ULL;
    unsigned long long total_cold = 0ULL;
    unsigned long long total_nonfinite = 0ULL;
    unsigned long long total_candidate_hot = 0ULL;
    unsigned long long total_candidate_cold = 0ULL;
    unsigned long long total_protected_hot = 0ULL;
    unsigned long long total_protected_cold = 0ULL;
    unsigned long long total_star_protected_hot = 0ULL;
    unsigned long long total_star_protected_cold = 0ULL;
    unsigned long long total_star_protected_cosmetic = 0ULL;
    unsigned long long total_star_count = 0ULL;
    for (std::size_t i = 0; i < frame_indices.size(); ++i) {
      std::array<unsigned long long, 10> counts{
          host_counts[i * 10ULL + 0ULL],
          host_counts[i * 10ULL + 1ULL],
          host_counts[i * 10ULL + 2ULL],
          host_counts[i * 10ULL + 3ULL],
          host_counts[i * 10ULL + 4ULL],
          host_counts[i * 10ULL + 5ULL],
          host_counts[i * 10ULL + 6ULL],
          host_counts[i * 10ULL + 7ULL],
          host_counts[i * 10ULL + 8ULL],
          host_counts[i * 10ULL + 9ULL]};
      total_hot += counts[0];
      total_cold += counts[1];
      total_nonfinite += counts[2];
      total_candidate_hot += counts[3];
      total_candidate_cold += counts[4];
      total_protected_hot += counts[5];
      total_protected_cold += counts[6];
      total_star_protected_hot += counts[7];
      total_star_protected_cold += counts[8];
      total_star_protected_cosmetic += counts[9];
      total_star_count += star_counts[i];
      py::dict frame_result = star_protected_isolated_cosmetic_result_dict(
          counts,
          native_method,
          static_cast<std::size_t>(frame_indices[i]),
          low_thresholds[i],
          high_thresholds[i],
          medians[i],
          sigmas[i],
          structure_sigma,
          min_neighbor_support,
          static_cast<std::size_t>(star_counts[i]),
          star_protection_radii[i],
          applied_mode);
      frame_result["per_frame_native_method"] = per_frame_native_method;
      frame_result["batch_position"] = static_cast<unsigned long long>(i);
      frame_result["mask_upload_s"] = 0.0;
      frame_result["threshold_upload_s"] = threshold_upload_s;
      frame_result["star_catalog_upload_s"] = star_catalog_upload_s;
      frame_result["star_catalog_upload_bytes"] = star_catalog_upload_bytes;
      frame_result["counts_memset_s"] = memset_s;
      frame_result["kernel_enqueue_s"] = kernel_s;
      frame_result["sync_s"] = sync_s;
      frame_result["device_counts_download_s"] = counts_download_s;
      frame_result["batch_single_kernel_launch"] = true;
      frame_result["batch_single_sync"] = true;
      frame_result["batch_frame_count"] = static_cast<unsigned long long>(frame_indices.size());
      frame_result["total_s"] = total_s;
      frame_result["detector_execution"] = detector_execution;
      frames.append(frame_result);
    }

    const unsigned long long total_cosmetic = total_hot + total_cold;
    const unsigned long long total_invalid = total_cosmetic + total_nonfinite;
    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = native_method;
    result["frame_count"] = static_cast<unsigned long long>(frame_indices.size());
    result["total_pixels_per_frame"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["star_count"] = total_star_count;
    result["hot_samples"] = total_hot;
    result["cold_samples"] = total_cold;
    result["nonfinite_samples"] = total_nonfinite;
    result["candidate_hot_samples"] = total_candidate_hot;
    result["candidate_cold_samples"] = total_candidate_cold;
    result["protected_hot_samples"] = total_protected_hot;
    result["protected_cold_samples"] = total_protected_cold;
    result["star_protected_hot_samples"] = total_star_protected_hot;
    result["star_protected_cold_samples"] = total_star_protected_cold;
    result["star_protected_cosmetic_samples"] = total_star_protected_cosmetic;
    result["cosmetic_corrected_samples"] = total_cosmetic;
    result["invalid_samples"] = total_invalid;
    result["applied"] = applied_mode && total_invalid > 0ULL;
    result["mask_upload_s"] = 0.0;
    result["threshold_upload_s"] = threshold_upload_s;
    result["star_catalog_upload_s"] = star_catalog_upload_s;
    result["star_catalog_upload_bytes"] = star_catalog_upload_bytes;
    result["counts_memset_s"] = memset_s;
    result["kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["device_counts_download_s"] = counts_download_s;
    result["batch_single_kernel_launch"] = true;
    result["batch_single_sync"] = true;
    result["star_catalog_source"] = "host_catalog_coordinates_device_batch_applied";
    result["detector_execution"] = detector_execution;
    result["total_s"] = total_s;
    result["structure_sigma"] = structure_sigma;
    result["min_neighbor_support"] = min_neighbor_support;
    result["frames"] = frames;
    return result;
  }

  py::dict apply_isolated_cosmetic_threshold_mask_frames(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj,
      py::iterable medians_obj,
      py::iterable sigmas_obj,
      float structure_sigma,
      int min_neighbor_support) {
    std::vector<unsigned long long> frame_indices;
    std::vector<float> low_thresholds;
    std::vector<float> high_thresholds;
    std::vector<float> medians;
    std::vector<float> sigmas;
    for (py::handle item : indices_obj) {
      const auto index = py::cast<std::size_t>(item);
      require_loaded(index, "resident source DQ batch isolated cosmetic threshold application");
      frame_indices.push_back(static_cast<unsigned long long>(index));
    }
    for (py::handle item : low_thresholds_obj) {
      low_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : high_thresholds_obj) {
      high_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : medians_obj) {
      medians.push_back(py::cast<float>(item));
    }
    for (py::handle item : sigmas_obj) {
      sigmas.push_back(py::cast<float>(item));
    }
    validate_isolated_batch_payload(frame_indices, low_thresholds, high_thresholds, medians, sigmas);

    const auto total_start = Clock::now();
    unsigned long long* d_indices = nullptr;
    float* d_low_thresholds = nullptr;
    float* d_high_thresholds = nullptr;
    float* d_medians = nullptr;
    float* d_sigmas = nullptr;
    unsigned long long* d_counts = nullptr;
    std::vector<unsigned long long> host_counts(frame_indices.size() * 7ULL, 0ULL);
    double upload_s = 0.0;
    double memset_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    if (!frame_indices.empty()) {
      try {
        allocate_isolated_batch_buffers(
            frame_indices, low_thresholds, high_thresholds, medians, sigmas,
            &d_indices, &d_low_thresholds, &d_high_thresholds, &d_medians, &d_sigmas,
            &d_counts, upload_s, memset_s, host_counts.size(), "application");
        const auto kernel_start = Clock::now();
        glass_apply_isolated_cosmetic_threshold_mask_frames_f32_launch(
            d_stack_, width_, height_, d_indices, d_low_thresholds, d_high_thresholds,
            d_medians, d_sigmas, frame_indices.size(), structure_sigma, min_neighbor_support, d_counts);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames kernel launch");
        kernel_s = seconds_since(kernel_start);
        const auto sync_start = Clock::now();
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames synchronize");
        sync_s = seconds_since(sync_start);
        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(host_counts.data(), d_counts, host_counts.size() * sizeof(unsigned long long), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch isolated cosmetic threshold counts)");
        counts_download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_indices);
        cudaFree(d_low_thresholds);
        cudaFree(d_high_thresholds);
        cudaFree(d_medians);
        cudaFree(d_sigmas);
        cudaFree(d_counts);
        throw;
      }
    }
    cudaFree(d_indices);
    cudaFree(d_low_thresholds);
    cudaFree(d_high_thresholds);
    cudaFree(d_medians);
    cudaFree(d_sigmas);
    cudaFree(d_counts);
    return isolated_cosmetic_batch_result_dict(
        host_counts, frame_indices, low_thresholds, high_thresholds, medians, sigmas,
        structure_sigma, min_neighbor_support,
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame",
        "cuda_isolated_threshold_apply_batch", true, upload_s, memset_s, kernel_s, sync_s,
        counts_download_s, seconds_since(total_start));
  }

  py::dict count_isolated_cosmetic_threshold_mask_frames(
      py::iterable indices_obj,
      py::iterable low_thresholds_obj,
      py::iterable high_thresholds_obj,
      py::iterable medians_obj,
      py::iterable sigmas_obj,
      float structure_sigma,
      int min_neighbor_support) const {
    std::vector<unsigned long long> frame_indices;
    std::vector<float> low_thresholds;
    std::vector<float> high_thresholds;
    std::vector<float> medians;
    std::vector<float> sigmas;
    for (py::handle item : indices_obj) {
      const auto index = py::cast<std::size_t>(item);
      require_loaded(index, "resident source DQ batch isolated cosmetic threshold count");
      frame_indices.push_back(static_cast<unsigned long long>(index));
    }
    for (py::handle item : low_thresholds_obj) {
      low_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : high_thresholds_obj) {
      high_thresholds.push_back(py::cast<float>(item));
    }
    for (py::handle item : medians_obj) {
      medians.push_back(py::cast<float>(item));
    }
    for (py::handle item : sigmas_obj) {
      sigmas.push_back(py::cast<float>(item));
    }
    validate_isolated_batch_payload(frame_indices, low_thresholds, high_thresholds, medians, sigmas);

    const auto total_start = Clock::now();
    unsigned long long* d_indices = nullptr;
    float* d_low_thresholds = nullptr;
    float* d_high_thresholds = nullptr;
    float* d_medians = nullptr;
    float* d_sigmas = nullptr;
    unsigned long long* d_counts = nullptr;
    std::vector<unsigned long long> host_counts(frame_indices.size() * 7ULL, 0ULL);
    double upload_s = 0.0;
    double memset_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double counts_download_s = 0.0;
    if (!frame_indices.empty()) {
      try {
        allocate_isolated_batch_buffers(
            frame_indices, low_thresholds, high_thresholds, medians, sigmas,
            &d_indices, &d_low_thresholds, &d_high_thresholds, &d_medians, &d_sigmas,
            &d_counts, upload_s, memset_s, host_counts.size(), "count");
        const auto kernel_start = Clock::now();
        glass_count_isolated_cosmetic_threshold_mask_frames_f32_launch(
            d_stack_, width_, height_, d_indices, d_low_thresholds, d_high_thresholds,
            d_medians, d_sigmas, frame_indices.size(), structure_sigma, min_neighbor_support, d_counts);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames kernel launch");
        kernel_s = seconds_since(kernel_start);
        const auto sync_start = Clock::now();
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames synchronize");
        sync_s = seconds_since(sync_start);
        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(host_counts.data(), d_counts, host_counts.size() * sizeof(unsigned long long), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch isolated cosmetic threshold count counts)");
        counts_download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_indices);
        cudaFree(d_low_thresholds);
        cudaFree(d_high_thresholds);
        cudaFree(d_medians);
        cudaFree(d_sigmas);
        cudaFree(d_counts);
        throw;
      }
    }
    cudaFree(d_indices);
    cudaFree(d_low_thresholds);
    cudaFree(d_high_thresholds);
    cudaFree(d_medians);
    cudaFree(d_sigmas);
    cudaFree(d_counts);
    return isolated_cosmetic_batch_result_dict(
        host_counts, frame_indices, low_thresholds, high_thresholds, medians, sigmas,
        structure_sigma, min_neighbor_support,
        "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames",
        "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame",
        "cuda_isolated_threshold_count_batch", false, upload_s, memset_s, kernel_s, sync_s,
        counts_download_s, seconds_since(total_start));
  }

  py::dict frame_histogram_robust_stats(
      std::size_t index,
      int bin_count,
      float hot_sigma,
      float cold_sigma) const {
    require_loaded(index, "resident histogram robust frame statistics");
    if (bin_count < 16 || bin_count > 65536) {
      throw std::invalid_argument("bin_count must be in [16, 65536]");
    }
    if (!(hot_sigma > 0.0f) || !(cold_sigma > 0.0f)) {
      throw std::invalid_argument("hot_sigma and cold_sigma must be positive");
    }

    const auto total_start = Clock::now();
    constexpr int threads = 256;
    const int reduction_blocks = std::min<int>(
        4096,
        std::max<int>(
            1,
            static_cast<int>((pixels_per_frame_ + static_cast<std::size_t>(threads) - 1) / threads)));
    const int histogram_blocks = reduction_blocks;
    float* d_partial_min = nullptr;
    float* d_partial_max = nullptr;
    unsigned long long* d_partial_count = nullptr;
    unsigned long long* d_histogram = nullptr;
    std::vector<float> partial_min(static_cast<std::size_t>(reduction_blocks), 0.0f);
    std::vector<float> partial_max(static_cast<std::size_t>(reduction_blocks), 0.0f);
    std::vector<unsigned long long> partial_count(static_cast<std::size_t>(reduction_blocks), 0ULL);
    std::vector<unsigned long long> histogram(static_cast<std::size_t>(bin_count), 0ULL);
    std::vector<unsigned long long> absdev_histogram(static_cast<std::size_t>(bin_count), 0ULL);
    double alloc_s = 0.0;
    double minmax_kernel_s = 0.0;
    double minmax_sync_s = 0.0;
    double minmax_download_s = 0.0;
    double value_histogram_s = 0.0;
    double value_histogram_sync_s = 0.0;
    double value_histogram_download_s = 0.0;
    double absdev_histogram_s = 0.0;
    double absdev_histogram_sync_s = 0.0;
    double absdev_histogram_download_s = 0.0;
    double host_bin_scan_s = 0.0;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(
          cudaMalloc(&d_partial_min, partial_min.size() * sizeof(float)),
          "cudaMalloc(resident histogram stats partial min)");
      check_cuda(
          cudaMalloc(&d_partial_max, partial_max.size() * sizeof(float)),
          "cudaMalloc(resident histogram stats partial max)");
      check_cuda(
          cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident histogram stats partial count)");
      check_cuda(
          cudaMalloc(&d_histogram, histogram.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident histogram stats histogram)");
      alloc_s = seconds_since(alloc_start);

      const auto minmax_start = Clock::now();
      glass_frame_minmax_count_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_partial_min,
          d_partial_max,
          d_partial_count,
          pixels_per_frame_,
          reduction_blocks);
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.frame_histogram_robust_stats minmax kernel launch");
      minmax_kernel_s = seconds_since(minmax_start);

      const auto minmax_sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.frame_histogram_robust_stats minmax synchronize");
      minmax_sync_s = seconds_since(minmax_sync_start);

      const auto minmax_download_start = Clock::now();
      check_cuda(
          cudaMemcpy(partial_min.data(), d_partial_min, partial_min.size() * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident histogram stats partial min)");
      check_cuda(
          cudaMemcpy(partial_max.data(), d_partial_max, partial_max.size() * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident histogram stats partial max)");
      check_cuda(
          cudaMemcpy(
              partial_count.data(),
              d_partial_count,
              partial_count.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident histogram stats partial count)");
      minmax_download_s = seconds_since(minmax_download_start);
    } catch (...) {
      cudaFree(d_partial_min);
      cudaFree(d_partial_max);
      cudaFree(d_partial_count);
      cudaFree(d_histogram);
      throw;
    }

    float finite_min = std::numeric_limits<float>::infinity();
    float finite_max = -std::numeric_limits<float>::infinity();
    unsigned long long finite_count = 0ULL;
    for (int i = 0; i < reduction_blocks; ++i) {
      const unsigned long long block_count = partial_count[static_cast<std::size_t>(i)];
      if (block_count == 0ULL) {
        continue;
      }
      finite_count += block_count;
      finite_min = std::min(finite_min, partial_min[static_cast<std::size_t>(i)]);
      finite_max = std::max(finite_max, partial_max[static_cast<std::size_t>(i)]);
    }

    double median = 0.0;
    double mad = 0.0;
    double sigma = 0.0;
    float low_threshold = -std::numeric_limits<float>::infinity();
    float high_threshold = std::numeric_limits<float>::infinity();
    bool sigma_fallback_used = false;
    double value_bin_width = 0.0;
    double absdev_bin_width = 0.0;
    if (finite_count > 0ULL) {
      if (!(finite_max > finite_min)) {
        median = static_cast<double>(finite_min);
        sigma = 1.0;
        sigma_fallback_used = true;
      } else {
        value_bin_width = (static_cast<double>(finite_max) - static_cast<double>(finite_min)) /
            static_cast<double>(bin_count);
        const float inv_value_bin_width = static_cast<float>(1.0 / value_bin_width);
        try {
          check_cuda(
              cudaMemset(d_histogram, 0, histogram.size() * sizeof(unsigned long long)),
              "cudaMemset(resident value histogram)");
          const auto histogram_start = Clock::now();
          glass_frame_histogram_f32_launch(
              d_stack_ + index * pixels_per_frame_,
              d_histogram,
              pixels_per_frame_,
              finite_min,
              inv_value_bin_width,
              bin_count,
              histogram_blocks);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.frame_histogram_robust_stats value histogram launch");
          value_histogram_s = seconds_since(histogram_start);

          const auto histogram_sync_start = Clock::now();
          check_cuda(
              cudaDeviceSynchronize(),
              "ResidentCalibratedStack.frame_histogram_robust_stats value histogram synchronize");
          value_histogram_sync_s = seconds_since(histogram_sync_start);

          const auto histogram_download_start = Clock::now();
          check_cuda(
              cudaMemcpy(
                  histogram.data(),
                  d_histogram,
                  histogram.size() * sizeof(unsigned long long),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident value histogram)");
          value_histogram_download_s = seconds_since(histogram_download_start);
        } catch (...) {
          cudaFree(d_partial_min);
          cudaFree(d_partial_max);
          cudaFree(d_partial_count);
          cudaFree(d_histogram);
          throw;
        }

        const auto host_scan_start = Clock::now();
        median = histogram_quantile_center(
            histogram,
            finite_count,
            static_cast<double>(finite_min),
            value_bin_width,
            0.5);
        host_bin_scan_s += seconds_since(host_scan_start);

        const double max_dev = std::max(
            std::fabs(static_cast<double>(finite_min) - median),
            std::fabs(static_cast<double>(finite_max) - median));
        if (!(max_dev > 0.0)) {
          sigma = 1.0;
          sigma_fallback_used = true;
        } else {
          absdev_bin_width = max_dev / static_cast<double>(bin_count);
          const float inv_absdev_bin_width = static_cast<float>(1.0 / absdev_bin_width);
          try {
            check_cuda(
                cudaMemset(d_histogram, 0, absdev_histogram.size() * sizeof(unsigned long long)),
                "cudaMemset(resident absdev histogram)");
            const auto absdev_start = Clock::now();
            glass_frame_absdev_histogram_f32_launch(
                d_stack_ + index * pixels_per_frame_,
                d_histogram,
                pixels_per_frame_,
                static_cast<float>(median),
                inv_absdev_bin_width,
                bin_count,
                histogram_blocks);
            check_cuda(
                cudaGetLastError(),
                "ResidentCalibratedStack.frame_histogram_robust_stats absdev histogram launch");
            absdev_histogram_s = seconds_since(absdev_start);

            const auto absdev_sync_start = Clock::now();
            check_cuda(
                cudaDeviceSynchronize(),
                "ResidentCalibratedStack.frame_histogram_robust_stats absdev histogram synchronize");
            absdev_histogram_sync_s = seconds_since(absdev_sync_start);

            const auto absdev_download_start = Clock::now();
            check_cuda(
                cudaMemcpy(
                    absdev_histogram.data(),
                    d_histogram,
                    absdev_histogram.size() * sizeof(unsigned long long),
                    cudaMemcpyDeviceToHost),
                "cudaMemcpy(resident absdev histogram)");
            absdev_histogram_download_s = seconds_since(absdev_download_start);
          } catch (...) {
            cudaFree(d_partial_min);
            cudaFree(d_partial_max);
            cudaFree(d_partial_count);
            cudaFree(d_histogram);
            throw;
          }
          const auto absdev_scan_start = Clock::now();
          mad = histogram_quantile_center(absdev_histogram, finite_count, 0.0, absdev_bin_width, 0.5);
          host_bin_scan_s += seconds_since(absdev_scan_start);
          sigma = 1.4826 * mad;
          if (sigma <= 0.0 || !std::isfinite(sigma)) {
            sigma = 1.0;
            sigma_fallback_used = true;
          }
        }
      }
      low_threshold = static_cast<float>(median - static_cast<double>(cold_sigma) * sigma);
      high_threshold = static_cast<float>(median + static_cast<double>(hot_sigma) * sigma);
    }
    cudaFree(d_partial_min);
    cudaFree(d_partial_max);
    cudaFree(d_partial_count);
    cudaFree(d_histogram);

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.frame_histogram_robust_stats";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["valid_pixels"] = finite_count;
    result["nonfinite_pixels"] = static_cast<unsigned long long>(pixels_per_frame_) - finite_count;
    result["bin_count"] = bin_count;
    result["finite_min"] = finite_count > 0ULL ? static_cast<double>(finite_min) : 0.0;
    result["finite_max"] = finite_count > 0ULL ? static_cast<double>(finite_max) : 0.0;
    result["value_bin_width"] = value_bin_width;
    result["absdev_bin_width"] = absdev_bin_width;
    result["median"] = median;
    result["mad"] = mad;
    result["sigma"] = sigma;
    result["sigma_fallback_used"] = sigma_fallback_used;
    result["hot_sigma"] = hot_sigma;
    result["cold_sigma"] = cold_sigma;
    result["low_threshold"] = low_threshold;
    result["high_threshold"] = high_threshold;
    result["stats_domain"] = "resident_calibrated_frame";
    result["threshold_source"] = "cuda_resident_histogram_median_mad_scalar";
    result["robust_stats_execution"] = "cuda_histogram_quantile_then_host_bin_scan_scalar";
    result["histogram_approximation"] = true;
    result["materializes_host_frame"] = false;
    result["histogram_download_bytes"] =
        static_cast<unsigned long long>(2ULL * static_cast<unsigned long long>(bin_count) * sizeof(unsigned long long));
    result["minmax_partial_download_bytes"] = static_cast<unsigned long long>(
        reduction_blocks * (2 * sizeof(float) + sizeof(unsigned long long)));
    result["device_alloc_s"] = alloc_s;
    result["minmax_kernel_enqueue_s"] = minmax_kernel_s;
    result["minmax_sync_s"] = minmax_sync_s;
    result["minmax_download_s"] = minmax_download_s;
    result["value_histogram_kernel_enqueue_s"] = value_histogram_s;
    result["value_histogram_sync_s"] = value_histogram_sync_s;
    result["value_histogram_download_s"] = value_histogram_download_s;
    result["absdev_histogram_kernel_enqueue_s"] = absdev_histogram_s;
    result["absdev_histogram_sync_s"] = absdev_histogram_sync_s;
    result["absdev_histogram_download_s"] = absdev_histogram_download_s;
    result["host_bin_scan_s"] = host_bin_scan_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict frames_histogram_robust_stats(
      py::iterable indices_obj,
      int bin_count,
      float hot_sigma,
      float cold_sigma) const {
    if (bin_count < 16 || bin_count > 65536) {
      throw std::invalid_argument("bin_count must be in [16, 65536]");
    }
    if (!(hot_sigma > 0.0f) || !(cold_sigma > 0.0f)) {
      throw std::invalid_argument("hot_sigma and cold_sigma must be positive");
    }
    std::vector<std::size_t> indices;
    for (py::handle item : indices_obj) {
      const auto index = py::cast<std::size_t>(item);
      require_loaded(index, "resident batch histogram robust frame statistics");
      indices.push_back(index);
    }

    const auto batch_total_start = Clock::now();
    constexpr int threads = 256;
    const int reduction_blocks = std::min<int>(
        4096,
        std::max<int>(
            1,
            static_cast<int>((pixels_per_frame_ + static_cast<std::size_t>(threads) - 1) / threads)));
    const int histogram_blocks = reduction_blocks;
    float* d_partial_min = nullptr;
    float* d_partial_max = nullptr;
    unsigned long long* d_partial_count = nullptr;
    unsigned long long* d_histogram = nullptr;
    std::vector<float> partial_min(static_cast<std::size_t>(reduction_blocks), 0.0f);
    std::vector<float> partial_max(static_cast<std::size_t>(reduction_blocks), 0.0f);
    std::vector<unsigned long long> partial_count(static_cast<std::size_t>(reduction_blocks), 0ULL);
    std::vector<unsigned long long> histogram(static_cast<std::size_t>(bin_count), 0ULL);
    std::vector<unsigned long long> absdev_histogram(static_cast<std::size_t>(bin_count), 0ULL);
    py::list frames;
    double alloc_s = 0.0;
    double total_minmax_kernel_s = 0.0;
    double total_minmax_sync_s = 0.0;
    double total_minmax_download_s = 0.0;
    double total_value_histogram_s = 0.0;
    double total_value_histogram_sync_s = 0.0;
    double total_value_histogram_download_s = 0.0;
    double total_absdev_histogram_s = 0.0;
    double total_absdev_histogram_sync_s = 0.0;
    double total_absdev_histogram_download_s = 0.0;
    double total_host_bin_scan_s = 0.0;
    unsigned long long total_valid_pixels = 0ULL;
    unsigned long long total_nonfinite_pixels = 0ULL;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(
          cudaMalloc(&d_partial_min, partial_min.size() * sizeof(float)),
          "cudaMalloc(resident batch histogram stats partial min)");
      check_cuda(
          cudaMalloc(&d_partial_max, partial_max.size() * sizeof(float)),
          "cudaMalloc(resident batch histogram stats partial max)");
      check_cuda(
          cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident batch histogram stats partial count)");
      check_cuda(
          cudaMalloc(&d_histogram, histogram.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident batch histogram stats histogram)");
      alloc_s = seconds_since(alloc_start);

      for (const std::size_t index : indices) {
        const auto frame_total_start = Clock::now();
        double minmax_kernel_s = 0.0;
        double minmax_sync_s = 0.0;
        double minmax_download_s = 0.0;
        double value_histogram_s = 0.0;
        double value_histogram_sync_s = 0.0;
        double value_histogram_download_s = 0.0;
        double absdev_histogram_s = 0.0;
        double absdev_histogram_sync_s = 0.0;
        double absdev_histogram_download_s = 0.0;
        double host_bin_scan_s = 0.0;

        const auto minmax_start = Clock::now();
        glass_frame_minmax_count_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_partial_min,
            d_partial_max,
            d_partial_count,
            pixels_per_frame_,
            reduction_blocks);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.frames_histogram_robust_stats minmax kernel launch");
        minmax_kernel_s = seconds_since(minmax_start);

        const auto minmax_sync_start = Clock::now();
        check_cuda(
            cudaDeviceSynchronize(),
            "ResidentCalibratedStack.frames_histogram_robust_stats minmax synchronize");
        minmax_sync_s = seconds_since(minmax_sync_start);

        const auto minmax_download_start = Clock::now();
        check_cuda(
            cudaMemcpy(partial_min.data(), d_partial_min, partial_min.size() * sizeof(float), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch histogram stats partial min)");
        check_cuda(
            cudaMemcpy(partial_max.data(), d_partial_max, partial_max.size() * sizeof(float), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch histogram stats partial max)");
        check_cuda(
            cudaMemcpy(
                partial_count.data(),
                d_partial_count,
                partial_count.size() * sizeof(unsigned long long),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch histogram stats partial count)");
        minmax_download_s = seconds_since(minmax_download_start);

        float finite_min = std::numeric_limits<float>::infinity();
        float finite_max = -std::numeric_limits<float>::infinity();
        unsigned long long finite_count = 0ULL;
        for (int i = 0; i < reduction_blocks; ++i) {
          const unsigned long long block_count = partial_count[static_cast<std::size_t>(i)];
          if (block_count == 0ULL) {
            continue;
          }
          finite_count += block_count;
          finite_min = std::min(finite_min, partial_min[static_cast<std::size_t>(i)]);
          finite_max = std::max(finite_max, partial_max[static_cast<std::size_t>(i)]);
        }

        double median = 0.0;
        double mad = 0.0;
        double sigma = 0.0;
        float low_threshold = -std::numeric_limits<float>::infinity();
        float high_threshold = std::numeric_limits<float>::infinity();
        bool sigma_fallback_used = false;
        double value_bin_width = 0.0;
        double absdev_bin_width = 0.0;
        if (finite_count > 0ULL) {
          if (!(finite_max > finite_min)) {
            median = static_cast<double>(finite_min);
            sigma = 1.0;
            sigma_fallback_used = true;
          } else {
            value_bin_width = (static_cast<double>(finite_max) - static_cast<double>(finite_min)) /
                static_cast<double>(bin_count);
            const float inv_value_bin_width = static_cast<float>(1.0 / value_bin_width);
            check_cuda(
                cudaMemset(d_histogram, 0, histogram.size() * sizeof(unsigned long long)),
                "cudaMemset(resident batch value histogram)");
            const auto histogram_start = Clock::now();
            glass_frame_histogram_f32_launch(
                d_stack_ + index * pixels_per_frame_,
                d_histogram,
                pixels_per_frame_,
                finite_min,
                inv_value_bin_width,
                bin_count,
                histogram_blocks);
            check_cuda(
                cudaGetLastError(),
                "ResidentCalibratedStack.frames_histogram_robust_stats value histogram launch");
            value_histogram_s = seconds_since(histogram_start);

            const auto histogram_sync_start = Clock::now();
            check_cuda(
                cudaDeviceSynchronize(),
                "ResidentCalibratedStack.frames_histogram_robust_stats value histogram synchronize");
            value_histogram_sync_s = seconds_since(histogram_sync_start);

            const auto histogram_download_start = Clock::now();
            check_cuda(
                cudaMemcpy(
                    histogram.data(),
                    d_histogram,
                    histogram.size() * sizeof(unsigned long long),
                    cudaMemcpyDeviceToHost),
                "cudaMemcpy(resident batch value histogram)");
            value_histogram_download_s = seconds_since(histogram_download_start);

            const auto host_scan_start = Clock::now();
            median = histogram_quantile_center(
                histogram,
                finite_count,
                static_cast<double>(finite_min),
                value_bin_width,
                0.5);
            host_bin_scan_s += seconds_since(host_scan_start);

            const double max_dev = std::max(
                std::fabs(static_cast<double>(finite_min) - median),
                std::fabs(static_cast<double>(finite_max) - median));
            if (!(max_dev > 0.0)) {
              sigma = 1.0;
              sigma_fallback_used = true;
            } else {
              absdev_bin_width = max_dev / static_cast<double>(bin_count);
              const float inv_absdev_bin_width = static_cast<float>(1.0 / absdev_bin_width);
              check_cuda(
                  cudaMemset(d_histogram, 0, absdev_histogram.size() * sizeof(unsigned long long)),
                  "cudaMemset(resident batch absdev histogram)");
              const auto absdev_start = Clock::now();
              glass_frame_absdev_histogram_f32_launch(
                  d_stack_ + index * pixels_per_frame_,
                  d_histogram,
                  pixels_per_frame_,
                  static_cast<float>(median),
                  inv_absdev_bin_width,
                  bin_count,
                  histogram_blocks);
              check_cuda(
                  cudaGetLastError(),
                  "ResidentCalibratedStack.frames_histogram_robust_stats absdev histogram launch");
              absdev_histogram_s = seconds_since(absdev_start);

              const auto absdev_sync_start = Clock::now();
              check_cuda(
                  cudaDeviceSynchronize(),
                  "ResidentCalibratedStack.frames_histogram_robust_stats absdev histogram synchronize");
              absdev_histogram_sync_s = seconds_since(absdev_sync_start);

              const auto absdev_download_start = Clock::now();
              check_cuda(
                  cudaMemcpy(
                      absdev_histogram.data(),
                      d_histogram,
                      absdev_histogram.size() * sizeof(unsigned long long),
                      cudaMemcpyDeviceToHost),
                  "cudaMemcpy(resident batch absdev histogram)");
              absdev_histogram_download_s = seconds_since(absdev_download_start);

              const auto absdev_scan_start = Clock::now();
              mad = histogram_quantile_center(absdev_histogram, finite_count, 0.0, absdev_bin_width, 0.5);
              host_bin_scan_s += seconds_since(absdev_scan_start);
              sigma = 1.4826 * mad;
              if (sigma <= 0.0 || !std::isfinite(sigma)) {
                sigma = 1.0;
                sigma_fallback_used = true;
              }
            }
          }
          low_threshold = static_cast<float>(median - static_cast<double>(cold_sigma) * sigma);
          high_threshold = static_cast<float>(median + static_cast<double>(hot_sigma) * sigma);
        }

        total_minmax_kernel_s += minmax_kernel_s;
        total_minmax_sync_s += minmax_sync_s;
        total_minmax_download_s += minmax_download_s;
        total_value_histogram_s += value_histogram_s;
        total_value_histogram_sync_s += value_histogram_sync_s;
        total_value_histogram_download_s += value_histogram_download_s;
        total_absdev_histogram_s += absdev_histogram_s;
        total_absdev_histogram_sync_s += absdev_histogram_sync_s;
        total_absdev_histogram_download_s += absdev_histogram_download_s;
        total_host_bin_scan_s += host_bin_scan_s;
        total_valid_pixels += finite_count;
        total_nonfinite_pixels += static_cast<unsigned long long>(pixels_per_frame_) - finite_count;

        py::dict frame_result;
        frame_result["schema_version"] = 1;
        frame_result["native_method"] = "ResidentCalibratedStack.frames_histogram_robust_stats";
        frame_result["per_frame_native_method"] = "ResidentCalibratedStack.frame_histogram_robust_stats";
        frame_result["frame_index"] = static_cast<unsigned long long>(index);
        frame_result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
        frame_result["valid_pixels"] = finite_count;
        frame_result["nonfinite_pixels"] = static_cast<unsigned long long>(pixels_per_frame_) - finite_count;
        frame_result["bin_count"] = bin_count;
        frame_result["finite_min"] = finite_count > 0ULL ? static_cast<double>(finite_min) : 0.0;
        frame_result["finite_max"] = finite_count > 0ULL ? static_cast<double>(finite_max) : 0.0;
        frame_result["value_bin_width"] = value_bin_width;
        frame_result["absdev_bin_width"] = absdev_bin_width;
        frame_result["median"] = median;
        frame_result["mad"] = mad;
        frame_result["sigma"] = sigma;
        frame_result["sigma_fallback_used"] = sigma_fallback_used;
        frame_result["hot_sigma"] = hot_sigma;
        frame_result["cold_sigma"] = cold_sigma;
        frame_result["low_threshold"] = low_threshold;
        frame_result["high_threshold"] = high_threshold;
        frame_result["stats_domain"] = "resident_calibrated_frame";
        frame_result["threshold_source"] = "cuda_resident_histogram_median_mad_scalar";
        frame_result["robust_stats_execution"] =
            "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar";
        frame_result["histogram_approximation"] = true;
        frame_result["materializes_host_frame"] = false;
        frame_result["batch_reuses_device_work_buffers"] = true;
        frame_result["histogram_download_bytes"] = static_cast<unsigned long long>(
            2ULL * static_cast<unsigned long long>(bin_count) * sizeof(unsigned long long));
        frame_result["minmax_partial_download_bytes"] = static_cast<unsigned long long>(
            reduction_blocks * (2 * sizeof(float) + sizeof(unsigned long long)));
        frame_result["device_alloc_s"] = 0.0;
        frame_result["batch_device_alloc_s"] = alloc_s;
        frame_result["minmax_kernel_enqueue_s"] = minmax_kernel_s;
        frame_result["minmax_sync_s"] = minmax_sync_s;
        frame_result["minmax_download_s"] = minmax_download_s;
        frame_result["value_histogram_kernel_enqueue_s"] = value_histogram_s;
        frame_result["value_histogram_sync_s"] = value_histogram_sync_s;
        frame_result["value_histogram_download_s"] = value_histogram_download_s;
        frame_result["absdev_histogram_kernel_enqueue_s"] = absdev_histogram_s;
        frame_result["absdev_histogram_sync_s"] = absdev_histogram_sync_s;
        frame_result["absdev_histogram_download_s"] = absdev_histogram_download_s;
        frame_result["host_bin_scan_s"] = host_bin_scan_s;
        frame_result["total_s"] = seconds_since(frame_total_start);
        frames.append(frame_result);
      }
    } catch (...) {
      cudaFree(d_partial_min);
      cudaFree(d_partial_max);
      cudaFree(d_partial_count);
      cudaFree(d_histogram);
      throw;
    }
    cudaFree(d_partial_min);
    cudaFree(d_partial_max);
    cudaFree(d_partial_count);
    cudaFree(d_histogram);

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.frames_histogram_robust_stats";
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["total_pixels_per_frame"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["bin_count"] = bin_count;
    result["hot_sigma"] = hot_sigma;
    result["cold_sigma"] = cold_sigma;
    result["threshold_source"] = "cuda_resident_histogram_median_mad_scalar";
    result["robust_stats_execution"] =
        "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar";
    result["stats_domain"] = "resident_calibrated_frame";
    result["histogram_approximation"] = true;
    result["materializes_host_frame"] = false;
    result["batch_reuses_device_work_buffers"] = true;
    result["valid_pixels"] = total_valid_pixels;
    result["nonfinite_pixels"] = total_nonfinite_pixels;
    result["histogram_download_bytes"] = static_cast<unsigned long long>(
        indices.size() * 2ULL * static_cast<unsigned long long>(bin_count) * sizeof(unsigned long long));
    result["minmax_partial_download_bytes"] = static_cast<unsigned long long>(
        indices.size() * static_cast<std::size_t>(reduction_blocks) *
        (2 * sizeof(float) + sizeof(unsigned long long)));
    result["device_alloc_s"] = alloc_s;
    result["minmax_kernel_enqueue_s"] = total_minmax_kernel_s;
    result["minmax_sync_s"] = total_minmax_sync_s;
    result["minmax_download_s"] = total_minmax_download_s;
    result["value_histogram_kernel_enqueue_s"] = total_value_histogram_s;
    result["value_histogram_sync_s"] = total_value_histogram_sync_s;
    result["value_histogram_download_s"] = total_value_histogram_download_s;
    result["absdev_histogram_kernel_enqueue_s"] = total_absdev_histogram_s;
    result["absdev_histogram_sync_s"] = total_absdev_histogram_sync_s;
    result["absdev_histogram_download_s"] = total_absdev_histogram_download_s;
    result["host_bin_scan_s"] = total_host_bin_scan_s;
    result["total_s"] = seconds_since(batch_total_start);
    result["frames"] = frames;
    return result;
  }

  py::dict frame_sampled_robust_stats(
      std::size_t index,
      std::size_t sample_limit,
      float hot_sigma,
      float cold_sigma) const {
    require_loaded(index, "resident sampled robust frame statistics");
    if (sample_limit == 0) {
      throw std::invalid_argument("sample_limit must be positive");
    }
    if (!(hot_sigma > 0.0f) || !(cold_sigma > 0.0f)) {
      throw std::invalid_argument("hot_sigma and cold_sigma must be positive");
    }

    const auto total_start = Clock::now();
    const std::size_t sample_count = std::min<std::size_t>(pixels_per_frame_, sample_limit);
    float* d_sample = nullptr;
    std::vector<float> host_sample(sample_count, 0.0f);
    double alloc_s = 0.0;
    double kernel_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    if (sample_count > 0) {
      try {
        const auto alloc_start = Clock::now();
        check_cuda(
            cudaMalloc(&d_sample, sample_count * sizeof(float)),
            "cudaMalloc(resident sampled robust stats buffer)");
        alloc_s = seconds_since(alloc_start);

        const auto kernel_start = Clock::now();
        glass_sample_frame_even_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_sample,
            pixels_per_frame_,
            sample_count);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.frame_sampled_robust_stats sample kernel launch");
        kernel_s = seconds_since(kernel_start);

        const auto sync_start = Clock::now();
        check_cuda(
            cudaDeviceSynchronize(),
            "ResidentCalibratedStack.frame_sampled_robust_stats synchronize");
        sync_s = seconds_since(sync_start);

        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(host_sample.data(), d_sample, sample_count * sizeof(float), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident sampled robust stats sample)");
        download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_sample);
        throw;
      }
      cudaFree(d_sample);
    }

    const auto host_stats_start = Clock::now();
    std::vector<float> finite;
    finite.reserve(sample_count);
    for (const float value : host_sample) {
      if (std::isfinite(value)) {
        finite.push_back(value);
      }
    }
    const std::size_t finite_count = finite.size();
    double median = 0.0;
    double mad = 0.0;
    double sigma = 0.0;
    double mean = 0.0;
    double stddev = 0.0;
    bool std_fallback_used = false;
    float low_threshold = -std::numeric_limits<float>::infinity();
    float high_threshold = std::numeric_limits<float>::infinity();
    if (!finite.empty()) {
      median = sorted_median_f32(finite);
      std::vector<float> deviations;
      deviations.reserve(finite.size());
      double sum = 0.0;
      double sum2 = 0.0;
      for (const float value : finite) {
        const double value_d = static_cast<double>(value);
        sum += value_d;
        sum2 += value_d * value_d;
        deviations.push_back(static_cast<float>(std::fabs(value_d - median)));
      }
      mean = sum / static_cast<double>(finite_count);
      double variance = sum2 / static_cast<double>(finite_count) - mean * mean;
      if (variance < 0.0) {
        variance = 0.0;
      }
      stddev = std::sqrt(variance);
      mad = sorted_median_f32(deviations);
      sigma = mad > 0.0 ? 1.4826 * mad : stddev;
      if (sigma <= 0.0 || !std::isfinite(sigma)) {
        sigma = 1.0;
        std_fallback_used = true;
      } else {
        std_fallback_used = mad <= 0.0;
      }
      low_threshold = static_cast<float>(median - static_cast<double>(cold_sigma) * sigma);
      high_threshold = static_cast<float>(median + static_cast<double>(hot_sigma) * sigma);
    }
    const double host_stats_s = seconds_since(host_stats_start);

    py::dict result;
    result["schema_version"] = 1;
    result["native_method"] = "ResidentCalibratedStack.frame_sampled_robust_stats";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["total_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["sample_limit"] = static_cast<unsigned long long>(sample_limit);
    result["sample_count"] = static_cast<unsigned long long>(sample_count);
    result["finite_sample_count"] = static_cast<unsigned long long>(finite_count);
    result["nonfinite_sample_count"] = static_cast<unsigned long long>(sample_count - finite_count);
    result["sample_fraction"] =
        pixels_per_frame_ == 0 ? 0.0 : static_cast<double>(sample_count) / static_cast<double>(pixels_per_frame_);
    result["all_pixels_sampled"] = sample_count == pixels_per_frame_;
    result["materializes_host_frame"] = false;
    result["sample_download_bytes"] = static_cast<unsigned long long>(sample_count * sizeof(float));
    result["stats_domain"] = "resident_calibrated_frame";
    result["threshold_source"] = "cuda_resident_sampled_median_mad_scalar";
    result["robust_stats_execution"] = "cuda_even_sample_then_host_median_mad_scalar";
    result["median"] = median;
    result["mad"] = mad;
    result["sigma"] = sigma;
    result["mean"] = mean;
    result["std"] = stddev;
    result["std_fallback_used"] = std_fallback_used;
    result["hot_sigma"] = hot_sigma;
    result["cold_sigma"] = cold_sigma;
    result["low_threshold"] = low_threshold;
    result["high_threshold"] = high_threshold;
    result["device_alloc_s"] = alloc_s;
    result["sample_kernel_enqueue_s"] = kernel_s;
    result["sync_s"] = sync_s;
    result["sample_download_s"] = download_s;
    result["host_scalar_stats_s"] = host_stats_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  void calibrate_frame(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    calibrate_frame_pageable_impl(index, light_info.ptr, params);
    mark_loaded(index);
  }

  py::dict calibrate_frame_timed(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    const ResidentCalibrationTiming timing =
        calibrate_frame_pageable_impl(index, light_info.ptr, params);
    mark_loaded(index);
    return calibration_timing_dict(timing, "pageable");
  }

  void calibrate_frame_pinned_async(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    calibrate_frame_pinned_async_impl(index, light_info.ptr, params);
    mark_loaded(index);
  }

  py::dict calibrate_frame_pinned_async_timed(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    const ResidentCalibrationTiming timing =
        calibrate_frame_pinned_async_impl(index, light_info.ptr, params);
    mark_loaded(index);
    return calibration_timing_dict(timing, "pinned_async");
  }

  py::dict calibrate_frame_host_async_timed(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> light,
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) {
    require_index(index);
    const py::buffer_info light_info = light.request();
    require_frame_shape(light_info, height_, width_);
    const CalibrationParameters params =
        calibration_parameters(light_exposure_s, dark_exposure_obj, policy_obj);

    const ResidentCalibrationTiming timing =
        calibrate_frame_host_async_impl(index, light_info.ptr, params);
    mark_loaded(index);
    return calibration_timing_dict(timing, "host_async");
  }

  py::dict calibrate_frames_host_async_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      py::object policy_obj) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_batch";
      out["event_mode"] = "reused_stack_events";
      out["timing_model"] = "single_stream_sequential_h2d_kernel_one_sync";
      out["frame_count"] = 0;
      out["host_copy_s"] = 0.0;
      out["h2d_s"] = 0.0;
      out["calibrate_store_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_pinned_bytes"] = host_pinned_bytes();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      check_cuda(
          cudaEventRecord(calibrate_h2d_start_, calibrate_stream_),
          "cudaEventRecord(resident batch calibration start)");
      for (std::size_t i = 0; i < frame_count; ++i) {
        check_cuda(
            cudaMemcpyAsync(
                d_light_,
                light_ptrs[i],
                frame_bytes,
                cudaMemcpyHostToDevice,
                calibrate_stream_),
            "cudaMemcpyAsync(resident batch host raw light)");
        glass_calibrate_tile_f32_launch_stream(
            d_light_,
            d_bias_,
            d_dark_,
            d_flat_,
            d_stack_ + indices[i] * pixels_per_frame_,
            pixels_per_frame_,
            has_bias_,
            has_dark_,
            has_flat_,
            params[i].master_dark_includes_bias,
            params[i].dark_scale,
            params[i].flat_floor,
            params[i].pedestal,
            calibrate_stream_);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frames_host_async kernel launch");
      }
      check_cuda(
          cudaEventRecord(calibrate_kernel_stop_, calibrate_stream_),
          "cudaEventRecord(resident batch calibration stop)");
      const auto sync_start = Clock::now();
      check_cuda(
          cudaStreamSynchronize(calibrate_stream_),
          "ResidentCalibratedStack.calibrate_frames_host_async synchronize");
      sync_s = seconds_since(sync_start);
      stream_s = cuda_event_elapsed_s(
          calibrate_h2d_start_,
          calibrate_kernel_stop_,
          "cudaEventElapsedTime(resident batch h2d calibration)");
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "host_async_batch");
    out["timing_model"] = "single_stream_sequential_h2d_kernel_one_sync";
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    return out;
  }

  py::dict calibrate_frames_host_async_multistream_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      py::object policy_obj) {
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_multistream_batch";
      out["event_mode"] = "reused_stack_lane_events";
      out["timing_model"] = "multi_stream_lanes_one_sync";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["frame_count"] = 0;
      out["host_copy_s"] = 0.0;
      out["h2d_s"] = 0.0;
      out["calibrate_store_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_pinned_bytes"] = host_pinned_bytes();
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_stream_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t lane_count =
        std::min<std::size_t>(static_cast<std::size_t>(stream_count), frame_count);
    ensure_calibration_lanes(lane_count);

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_used(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      for (std::size_t i = 0; i < frame_count; ++i) {
        const std::size_t lane = i % lane_count;
        if (!lane_used[lane]) {
          check_cuda(
              cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident multistream batch lane start)");
          lane_used[lane] = 1;
        }
        check_cuda(
            cudaMemcpyAsync(
                d_calibration_lane_lights_[lane],
                light_ptrs[i],
                frame_bytes,
                cudaMemcpyHostToDevice,
                calibration_lane_streams_[lane]),
            "cudaMemcpyAsync(resident multistream batch host raw light)");
        glass_calibrate_tile_f32_launch_stream(
            d_calibration_lane_lights_[lane],
            d_bias_,
            d_dark_,
            d_flat_,
            d_stack_ + indices[i] * pixels_per_frame_,
            pixels_per_frame_,
            has_bias_,
            has_dark_,
            has_flat_,
            params[i].master_dark_includes_bias,
            params[i].dark_scale,
            params[i].flat_floor,
            params[i].pedestal,
            calibration_lane_streams_[lane]);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frames_host_async_multistream kernel launch");
      }
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_used[lane]) {
          check_cuda(
              cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident multistream batch lane stop)");
        }
      }
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_used[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_host_async_multistream synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_used[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident multistream batch lane)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "host_async_multistream_batch");
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    out["event_mode"] = "reused_stack_lane_events";
    out["timing_model"] = "multi_stream_lanes_one_sync";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_host_async_multistream_h2d_release_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_multistream_h2d_release_batch";
      out["event_mode"] = "reused_stack_lane_h2d_events";
      out["timing_model"] = "multi_stream_one_frame_per_lane_h2d_release_then_wait";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["frame_count"] = 0;
      out["h2d_release_s"] = 0.0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["pending"] = false;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_h2d_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t lane_count =
        std::min<std::size_t>(static_cast<std::size_t>(stream_count), frame_count);
    if (frame_count > lane_count) {
      throw std::invalid_argument(
          "h2d-release calibration requires frame_count <= stream_count so each lane holds one frame");
    }
    ensure_calibration_lanes(lane_count);

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_used(lane_count, 0);
    std::vector<double> lane_h2d_elapsed(lane_count, 0.0);
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    {
      py::gil_scoped_release release;
      try {
        for (std::size_t i = 0; i < frame_count; ++i) {
          const std::size_t lane = i;
          check_cuda(
              cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident h2d-release lane start)");
          lane_used[lane] = 1;
          check_cuda(
              cudaMemcpyAsync(
                  d_calibration_lane_lights_[lane],
                  light_ptrs[i],
                  frame_bytes,
                  cudaMemcpyHostToDevice,
                  calibration_lane_streams_[lane]),
              "cudaMemcpyAsync(resident h2d-release host raw light)");
          check_cuda(
              cudaEventRecord(calibration_lane_h2d_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident h2d-release lane h2d done)");
          glass_calibrate_tile_f32_launch_stream(
              d_calibration_lane_lights_[lane],
              d_bias_,
              d_dark_,
              d_flat_,
              d_stack_ + indices[i] * pixels_per_frame_,
              pixels_per_frame_,
              has_bias_,
              has_dark_,
              has_flat_,
              params[i].master_dark_includes_bias,
              params[i].dark_scale,
              params[i].flat_floor,
              params[i].pedestal,
              calibration_lane_streams_[lane]);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.calibrate_frames_host_async_multistream_h2d_release kernel launch");
          check_cuda(
              cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident h2d-release lane calibration stop)");
        }
        const auto h2d_sync_start = Clock::now();
        for (std::size_t lane = 0; lane < lane_count; ++lane) {
          if (lane_used[lane]) {
            check_cuda(
                cudaEventSynchronize(calibration_lane_h2d_events_[lane]),
                "cudaEventSynchronize(resident h2d-release lane h2d)");
          }
        }
        h2d_event_sync_s = seconds_since(h2d_sync_start);
        for (std::size_t lane = 0; lane < lane_count; ++lane) {
          if (lane_used[lane]) {
            lane_h2d_elapsed[lane] = cuda_event_elapsed_s(
                calibration_lane_start_events_[lane],
                calibration_lane_h2d_events_[lane],
                "cudaEventElapsedTime(resident h2d-release lane h2d)");
            h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_elapsed[lane]);
          }
        }
      } catch (...) {
        for (std::size_t lane = 0; lane < lane_count; ++lane) {
          if (lane_used[lane]) {
            cudaStreamSynchronize(calibration_lane_streams_[lane]);
          }
        }
        throw;
      }
    }

    pending_calibration_ = true;
    pending_calibration_indices_ = indices;
    pending_calibration_lane_used_ = lane_used;
    pending_calibration_lane_count_ = lane_count;
    pending_calibration_total_start_ = total_start;
    pending_calibration_h2d_release_s_ = seconds_since(total_start);
    pending_calibration_h2d_event_sync_s_ = h2d_event_sync_s;
    pending_calibration_h2d_event_elapsed_s_ = h2d_event_elapsed_s;

    py::list lane_h2d_elapsed_s;
    for (const double value : lane_h2d_elapsed) {
      lane_h2d_elapsed_s.append(value);
    }
    py::dict out;
    out["schema_version"] = 1;
    out["h2d_mode"] = "host_async_multistream_h2d_release_batch";
    out["event_mode"] = "reused_stack_lane_h2d_events";
    out["timing_model"] = "multi_stream_one_frame_per_lane_h2d_release_then_wait";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["h2d_release_s"] = pending_calibration_h2d_release_s_;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["total_s"] = pending_calibration_h2d_release_s_;
    out["host_release_safe"] = true;
    out["pending"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_h2d_elapsed_s"] = lane_h2d_elapsed_s;
    return out;
  }

  py::dict finish_pending_calibration_timed() {
    if (!pending_calibration_) {
      py::dict out;
      out["schema_version"] = 1;
      out["pending"] = false;
      out["wait_sync_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["total_s"] = 0.0;
      out["frame_count"] = 0;
      out["stream_count"] = 0;
      out["lane_stream_elapsed_s"] = py::list();
      return out;
    }
    double wait_sync_s = 0.0;
    double stream_s = 0.0;
    std::vector<double> lane_elapsed(pending_calibration_lane_count_, 0.0);
    {
      py::gil_scoped_release release;
      const auto wait_start = Clock::now();
      for (std::size_t lane = 0; lane < pending_calibration_lane_count_; ++lane) {
        if (pending_calibration_lane_used_[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.finish_pending_calibration synchronize");
        }
      }
      wait_sync_s = seconds_since(wait_start);
      for (std::size_t lane = 0; lane < pending_calibration_lane_count_; ++lane) {
        if (pending_calibration_lane_used_[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident h2d-release lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : pending_calibration_indices_) {
      mark_loaded(index);
    }
    const double total_s = seconds_since(pending_calibration_total_start_);
    const std::size_t frame_count = pending_calibration_indices_.size();
    const std::size_t stream_count = pending_calibration_lane_count_;
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }

    pending_calibration_ = false;
    pending_calibration_indices_.clear();
    pending_calibration_lane_used_.clear();
    pending_calibration_lane_count_ = 0;

    py::dict out;
    out["schema_version"] = 1;
    out["pending"] = false;
    out["event_mode"] = "reused_stack_lane_h2d_events";
    out["timing_model"] = "multi_stream_one_frame_per_lane_h2d_release_then_wait";
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["stream_count"] = static_cast<unsigned long long>(stream_count);
    out["h2d_release_s"] = pending_calibration_h2d_release_s_;
    out["h2d_event_sync_s"] = pending_calibration_h2d_event_sync_s_;
    out["h2d_event_elapsed_s"] = pending_calibration_h2d_event_elapsed_s_;
    out["wait_sync_s"] = wait_sync_s;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = wait_sync_s;
    out["total_s"] = total_s;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_host_async_multistream_callback_release_timed(
      py::object indices_obj,
      py::object lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      int wave_frames,
      py::object release_callback,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    if (wave_frames <= 0) {
      throw std::invalid_argument("wave_frames must be positive");
    }
    if (wave_frames > stream_count) {
      throw std::invalid_argument("callback-release calibration requires wave_frames <= stream_count");
    }
    if (!PyCallable_Check(release_callback.ptr())) {
      throw std::invalid_argument("release_callback must be callable");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence lights = py::cast<py::sequence>(lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "host_async_multistream_callback_release_batch";
      out["event_mode"] = "reused_stack_lane_h2d_callback_events";
      out["timing_model"] = "multi_stream_callback_release_waves_one_final_sync";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["requested_wave_frames"] = wave_frames;
      out["wave_frames"] = 0;
      out["wave_frames_clamped_to_stream_count"] = false;
      out["wave_count"] = 0;
      out["frame_count"] = 0;
      out["callback_release_count"] = 0;
      out["h2d_release_s"] = 0.0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["callback_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_stream_elapsed_s"] = py::list();
      out["wave_h2d_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t requested_wave_frames = static_cast<std::size_t>(wave_frames);
    const std::size_t stream_limit = static_cast<std::size_t>(stream_count);
    const std::size_t effective_wave_frames =
        std::min<std::size_t>(std::min<std::size_t>(requested_wave_frames, stream_limit), frame_count);
    const bool wave_frames_clamped_to_stream_count = requested_wave_frames > stream_limit;
    const std::size_t lane_count = std::min<std::size_t>(stream_limit, effective_wave_frames);
    ensure_calibration_lanes(lane_count);

    std::vector<py::array_t<float, py::array::c_style | py::array::forcecast>> light_arrays;
    std::vector<void*> light_ptrs;
    std::vector<CalibrationParameters> params;
    light_arrays.reserve(frame_count);
    light_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto light = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(lights[i]);
      const py::buffer_info info = light.request();
      require_frame_shape(info, height_, width_);
      light_ptrs.push_back(info.ptr);
      light_arrays.push_back(std::move(light));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_started(lane_count, 0);
    std::vector<unsigned char> lane_used_in_wave(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    std::vector<double> wave_h2d_elapsed;
    wave_h2d_elapsed.reserve((frame_count + effective_wave_frames - 1) / effective_wave_frames);
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    double callback_s = 0.0;
    std::size_t callback_release_count = 0;
    std::size_t wave_count = 0;
    double h2d_release_s = 0.0;
    try {
      for (std::size_t wave_start = 0; wave_start < frame_count; wave_start += effective_wave_frames) {
        const std::size_t frames_in_wave = std::min<std::size_t>(effective_wave_frames, frame_count - wave_start);
        std::fill(lane_used_in_wave.begin(), lane_used_in_wave.end(), 0);
        double wave_elapsed_s = 0.0;
        {
          py::gil_scoped_release release;
          for (std::size_t j = 0; j < frames_in_wave; ++j) {
            const std::size_t lane = j;
            const std::size_t frame_offset = wave_start + j;
            if (!lane_started[lane]) {
              check_cuda(
                  cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
                  "cudaEventRecord(resident callback-release lane start)");
              lane_started[lane] = 1;
            }
            lane_used_in_wave[lane] = 1;
            check_cuda(
                cudaEventRecord(calibration_lane_h2d_start_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident callback-release lane h2d start)");
            check_cuda(
                cudaMemcpyAsync(
                    d_calibration_lane_lights_[lane],
                    light_ptrs[frame_offset],
                    frame_bytes,
                    cudaMemcpyHostToDevice,
                    calibration_lane_streams_[lane]),
                "cudaMemcpyAsync(resident callback-release host raw light)");
            check_cuda(
                cudaEventRecord(calibration_lane_h2d_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident callback-release lane h2d done)");
            glass_calibrate_tile_f32_launch_stream(
                d_calibration_lane_lights_[lane],
                d_bias_,
                d_dark_,
                d_flat_,
                d_stack_ + indices[frame_offset] * pixels_per_frame_,
                pixels_per_frame_,
                has_bias_,
                has_dark_,
                has_flat_,
                params[frame_offset].master_dark_includes_bias,
                params[frame_offset].dark_scale,
                params[frame_offset].flat_floor,
                params[frame_offset].pedestal,
                calibration_lane_streams_[lane]);
            check_cuda(
                cudaGetLastError(),
                "ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release kernel launch");
            check_cuda(
                cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident callback-release lane calibration stop)");
          }
          const auto h2d_sync_start = Clock::now();
          for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
            if (lane_used_in_wave[lane]) {
              check_cuda(
                  cudaEventSynchronize(calibration_lane_h2d_events_[lane]),
                  "cudaEventSynchronize(resident callback-release lane h2d)");
            }
          }
          h2d_event_sync_s += seconds_since(h2d_sync_start);
          for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
            if (lane_used_in_wave[lane]) {
              const double lane_h2d_s = cuda_event_elapsed_s(
                  calibration_lane_h2d_start_events_[lane],
                  calibration_lane_h2d_events_[lane],
                  "cudaEventElapsedTime(resident callback-release lane h2d)");
              wave_elapsed_s = std::max(wave_elapsed_s, lane_h2d_s);
              h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_s);
            }
          }
        }
        py::list released_indices;
        for (std::size_t j = 0; j < frames_in_wave; ++j) {
          released_indices.append(static_cast<unsigned long long>(indices[wave_start + j]));
        }
        const auto callback_start = Clock::now();
        release_callback(released_indices);
        callback_s += seconds_since(callback_start);
        callback_release_count += frames_in_wave;
        wave_h2d_elapsed.push_back(wave_elapsed_s);
        ++wave_count;
      }
      h2d_release_s = seconds_since(total_start);
    } catch (...) {
      py::gil_scoped_release release;
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          cudaStreamSynchronize(calibration_lane_streams_[lane]);
        }
      }
      throw;
    }

    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident callback-release lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    py::list wave_h2d_elapsed_s;
    for (const double value : wave_h2d_elapsed) {
      wave_h2d_elapsed_s.append(value);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "host_async_multistream_callback_release_batch");
    out["event_mode"] = "reused_stack_lane_h2d_callback_events";
    out["timing_model"] = "multi_stream_callback_release_waves_one_final_sync";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["requested_wave_frames"] = wave_frames;
    out["wave_frames"] = static_cast<unsigned long long>(effective_wave_frames);
    out["wave_frames_clamped_to_stream_count"] = wave_frames_clamped_to_stream_count;
    out["wave_count"] = static_cast<unsigned long long>(wave_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["callback_release_count"] = static_cast<unsigned long long>(callback_release_count);
    out["h2d_release_s"] = h2d_release_s;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["callback_s"] = callback_s;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["host_release_safe"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    out["wave_h2d_elapsed_s"] = wave_h2d_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed(
      py::object indices_obj,
      py::object raw_lights_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      int wave_frames,
      py::object release_callback,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    if (wave_frames <= 0) {
      throw std::invalid_argument("wave_frames must be positive");
    }
    if (wave_frames > stream_count) {
      throw std::invalid_argument("raw callback-release calibration requires wave_frames <= stream_count");
    }
    if (!PyCallable_Check(release_callback.ptr())) {
      throw std::invalid_argument("release_callback must be callable");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    py::sequence raw_lights = py::cast<py::sequence>(raw_lights_obj);
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "fits_u16be_bzero_gpu_decode_callback_release_batch";
      out["event_mode"] = "reused_stack_lane_h2d_callback_events";
      out["timing_model"] = "raw_u16be_h2d_gpu_decode_multi_stream_callback_release_waves_one_final_sync";
      out["source_sample_format"] = "fits_bitpix16_bzero32768_big_endian";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["requested_wave_frames"] = wave_frames;
      out["wave_frames"] = 0;
      out["wave_frames_clamped_to_stream_count"] = false;
      out["wave_count"] = 0;
      out["frame_count"] = 0;
      out["callback_release_count"] = 0;
      out["raw_h2d_bytes"] = 0;
      out["float32_host_bytes_avoided"] = 0;
      out["h2d_release_s"] = 0.0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["callback_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["lane_stream_elapsed_s"] = py::list();
      out["wave_h2d_elapsed_s"] = py::list();
      return out;
    }
    if (static_cast<std::size_t>(py::len(raw_lights)) != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument("indices, raw_lights, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t requested_wave_frames = static_cast<std::size_t>(wave_frames);
    const std::size_t stream_limit = static_cast<std::size_t>(stream_count);
    const std::size_t effective_wave_frames =
        std::min<std::size_t>(std::min<std::size_t>(requested_wave_frames, stream_limit), frame_count);
    const bool wave_frames_clamped_to_stream_count = requested_wave_frames > stream_limit;
    const std::size_t lane_count = std::min<std::size_t>(stream_limit, effective_wave_frames);
    ensure_calibration_lanes(lane_count);

    const std::size_t raw_frame_bytes = pixels_per_frame_ * 2u;
    std::vector<py::array_t<unsigned char, py::array::c_style | py::array::forcecast>> raw_arrays;
    std::vector<void*> raw_ptrs;
    std::vector<CalibrationParameters> params;
    raw_arrays.reserve(frame_count);
    raw_ptrs.reserve(frame_count);
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      auto raw = py::cast<py::array_t<unsigned char, py::array::c_style | py::array::forcecast>>(raw_lights[i]);
      const py::buffer_info info = raw.request();
      if (info.ndim != 1 || static_cast<std::size_t>(info.shape[0]) != raw_frame_bytes) {
        throw std::invalid_argument("raw FITS light buffer must be a 1D uint8 array of height*width*2 bytes");
      }
      raw_ptrs.push_back(info.ptr);
      raw_arrays.push_back(std::move(raw));
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_started(lane_count, 0);
    std::vector<unsigned char> lane_used_in_wave(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    std::vector<double> wave_h2d_elapsed;
    wave_h2d_elapsed.reserve((frame_count + effective_wave_frames - 1) / effective_wave_frames);
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    double callback_s = 0.0;
    std::size_t callback_release_count = 0;
    std::size_t wave_count = 0;
    double h2d_release_s = 0.0;
    try {
      for (std::size_t wave_start = 0; wave_start < frame_count; wave_start += effective_wave_frames) {
        const std::size_t frames_in_wave = std::min<std::size_t>(effective_wave_frames, frame_count - wave_start);
        std::fill(lane_used_in_wave.begin(), lane_used_in_wave.end(), 0);
        double wave_elapsed_s = 0.0;
        {
          py::gil_scoped_release release;
          for (std::size_t j = 0; j < frames_in_wave; ++j) {
            const std::size_t lane = j;
            const std::size_t frame_offset = wave_start + j;
            if (!lane_started[lane]) {
              check_cuda(
                  cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
                  "cudaEventRecord(resident raw callback-release lane start)");
              lane_started[lane] = 1;
            }
            lane_used_in_wave[lane] = 1;
            auto* lane_raw = reinterpret_cast<unsigned char*>(d_calibration_lane_lights_[lane]);
            check_cuda(
                cudaEventRecord(calibration_lane_h2d_start_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident raw callback-release lane h2d start)");
            check_cuda(
                cudaMemcpyAsync(
                    lane_raw,
                    raw_ptrs[frame_offset],
                    raw_frame_bytes,
                    cudaMemcpyHostToDevice,
                    calibration_lane_streams_[lane]),
                "cudaMemcpyAsync(resident raw callback-release FITS u16 light)");
            check_cuda(
                cudaEventRecord(calibration_lane_h2d_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident raw callback-release lane h2d done)");
            glass_calibrate_fits_u16be_bzero_f32_launch_stream(
                lane_raw,
                d_bias_,
                d_dark_,
                d_flat_,
                d_stack_ + indices[frame_offset] * pixels_per_frame_,
                pixels_per_frame_,
                has_bias_,
                has_dark_,
                has_flat_,
                params[frame_offset].master_dark_includes_bias,
                params[frame_offset].dark_scale,
                params[frame_offset].flat_floor,
                params[frame_offset].pedestal,
                calibration_lane_streams_[lane]);
            check_cuda(
                cudaGetLastError(),
                "ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_callback_release kernel launch");
            check_cuda(
                cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident raw callback-release lane calibration stop)");
          }
          const auto h2d_sync_start = Clock::now();
          for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
            if (lane_used_in_wave[lane]) {
              check_cuda(
                  cudaEventSynchronize(calibration_lane_h2d_events_[lane]),
                  "cudaEventSynchronize(resident raw callback-release lane h2d)");
            }
          }
          h2d_event_sync_s += seconds_since(h2d_sync_start);
          for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
            if (lane_used_in_wave[lane]) {
              const double lane_h2d_s = cuda_event_elapsed_s(
                  calibration_lane_h2d_start_events_[lane],
                  calibration_lane_h2d_events_[lane],
                  "cudaEventElapsedTime(resident raw callback-release lane h2d)");
              wave_elapsed_s = std::max(wave_elapsed_s, lane_h2d_s);
              h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_s);
            }
          }
        }
        py::list released_indices;
        for (std::size_t j = 0; j < frames_in_wave; ++j) {
          released_indices.append(static_cast<unsigned long long>(indices[wave_start + j]));
        }
        const auto callback_start = Clock::now();
        release_callback(released_indices);
        callback_s += seconds_since(callback_start);
        callback_release_count += frames_in_wave;
        wave_h2d_elapsed.push_back(wave_elapsed_s);
        ++wave_count;
      }
      h2d_release_s = seconds_since(total_start);
    } catch (...) {
      py::gil_scoped_release release;
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          cudaStreamSynchronize(calibration_lane_streams_[lane]);
        }
      }
      throw;
    }

    double sync_s = 0.0;
    double stream_s = 0.0;
    {
      py::gil_scoped_release release;
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_callback_release synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident raw callback-release lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    py::list wave_h2d_elapsed_s;
    for (const double value : wave_h2d_elapsed) {
      wave_h2d_elapsed_s.append(value);
    }
    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "fits_u16be_bzero_gpu_decode_callback_release_batch");
    out["event_mode"] = "reused_stack_lane_h2d_callback_events";
    out["timing_model"] = "raw_u16be_h2d_gpu_decode_multi_stream_callback_release_waves_one_final_sync";
    out["source_sample_format"] = "fits_bitpix16_bzero32768_big_endian";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["requested_wave_frames"] = wave_frames;
    out["wave_frames"] = static_cast<unsigned long long>(effective_wave_frames);
    out["wave_frames_clamped_to_stream_count"] = wave_frames_clamped_to_stream_count;
    out["wave_count"] = static_cast<unsigned long long>(wave_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["callback_release_count"] = static_cast<unsigned long long>(callback_release_count);
    out["raw_h2d_bytes"] = static_cast<unsigned long long>(raw_frame_bytes * frame_count);
    out["float32_host_bytes_avoided"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float) * frame_count);
    out["h2d_release_s"] = h2d_release_s;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["callback_s"] = callback_s;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["host_release_safe"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    out["wave_h2d_elapsed_s"] = wave_h2d_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_fits_u16be_bzero_paths_multistream_timed(
      py::object indices_obj,
      py::object paths_obj,
      py::object data_offsets_obj,
      py::object byte_counts_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      int wave_frames,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    if (wave_frames <= 0) {
      throw std::invalid_argument("wave_frames must be positive");
    }
    if (wave_frames > stream_count) {
      throw std::invalid_argument("native path-read calibration requires wave_frames <= stream_count");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto paths = py::cast<std::vector<std::string>>(paths_obj);
    const auto data_offsets = py::cast<std::vector<unsigned long long>>(data_offsets_obj);
    const auto byte_counts = py::cast<std::vector<unsigned long long>>(byte_counts_obj);
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "fits_u16be_bzero_native_path_read_calibration_batch";
      out["event_mode"] = "native_path_read_reused_stack_lane_events";
      out["timing_model"] = "native_path_read_wave_then_h2d_gpu_decode_calibration";
      out["source_sample_format"] = "fits_bitpix16_bzero32768_big_endian";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["requested_wave_frames"] = wave_frames;
      out["wave_frames"] = 0;
      out["wave_frames_clamped_to_stream_count"] = false;
      out["wave_count"] = 0;
      out["frame_count"] = 0;
      out["raw_h2d_bytes"] = 0;
      out["float32_host_bytes_avoided"] = 0;
      out["native_path_read_file_open_s"] = 0.0;
      out["native_path_read_file_read_s"] = 0.0;
      out["native_path_read_total_s"] = 0.0;
      out["native_path_read_bytes"] = 0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["native_path_host_buffer_bytes"] = 0;
      out["native_path_host_buffer_model"] = "none";
      out["native_path_host_buffer_pinned"] = false;
      out["lane_stream_elapsed_s"] = py::list();
      out["wave_h2d_elapsed_s"] = py::list();
      return out;
    }
    if (paths.size() != frame_count ||
        data_offsets.size() != frame_count ||
        byte_counts.size() != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument(
          "indices, paths, offsets, byte_counts, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t raw_frame_bytes = pixels_per_frame_ * 2u;
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      if (byte_counts[i] != static_cast<unsigned long long>(raw_frame_bytes)) {
        throw std::invalid_argument("native path-read FITS byte count must equal height*width*2");
      }
    }

    const std::size_t requested_wave_frames = static_cast<std::size_t>(wave_frames);
    const std::size_t stream_limit = static_cast<std::size_t>(stream_count);
    const std::size_t effective_wave_frames =
        std::min<std::size_t>(std::min<std::size_t>(requested_wave_frames, stream_limit), frame_count);
    const bool wave_frames_clamped_to_stream_count = requested_wave_frames > stream_limit;
    const std::size_t lane_count = std::min<std::size_t>(stream_limit, effective_wave_frames);
    ensure_calibration_lanes(lane_count);

    std::vector<std::unique_ptr<unsigned char, CudaHostUCharFree>> lane_host_buffers;
    lane_host_buffers.reserve(lane_count);
    for (std::size_t lane = 0; lane < lane_count; ++lane) {
      unsigned char* buffer = nullptr;
      check_cuda(
          cudaHostAlloc(
              reinterpret_cast<void**>(&buffer),
              raw_frame_bytes,
              cudaHostAllocPortable),
          "cudaHostAlloc(resident native path-read raw FITS lane buffer)");
      lane_host_buffers.emplace_back(buffer);
    }
    std::vector<CalibrationParameters> params;
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_started(lane_count, 0);
    std::vector<unsigned char> lane_used_in_wave(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    std::vector<double> wave_h2d_elapsed;
    wave_h2d_elapsed.reserve((frame_count + effective_wave_frames - 1) / effective_wave_frames);
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    double stream_s = 0.0;
    double native_open_s = 0.0;
    double native_read_s = 0.0;
    double native_total_read_s = 0.0;
    unsigned long long native_bytes_read = 0;
    std::size_t wave_count = 0;

    try {
      py::gil_scoped_release release;
      for (std::size_t wave_start = 0; wave_start < frame_count; wave_start += effective_wave_frames) {
        const std::size_t frames_in_wave = std::min<std::size_t>(effective_wave_frames, frame_count - wave_start);
        std::fill(lane_used_in_wave.begin(), lane_used_in_wave.end(), 0);
        std::vector<RawFitsReadTiming> read_timings(frames_in_wave);
        std::vector<std::string> read_errors(frames_in_wave);
        std::vector<std::thread> read_threads;
        read_threads.reserve(frames_in_wave);
        const auto wave_read_start = Clock::now();
        for (std::size_t j = 0; j < frames_in_wave; ++j) {
          read_threads.emplace_back([&, j]() {
            const std::size_t frame_offset = wave_start + j;
            try {
              read_timings[j] = read_raw_fits_bytes_into_ptr(
                  paths[frame_offset],
                  data_offsets[frame_offset],
                  raw_frame_bytes,
                  lane_host_buffers[j].get());
            } catch (const std::exception& exc) {
              read_errors[j] = exc.what();
            } catch (...) {
              read_errors[j] = "unknown native path-read calibration read error";
            }
          });
        }
        for (auto& thread : read_threads) {
          thread.join();
        }
        native_total_read_s += seconds_since(wave_read_start);
        for (std::size_t j = 0; j < frames_in_wave; ++j) {
          if (!read_errors[j].empty()) {
            std::ostringstream message;
            message << "native path-read calibration failed for frame "
                    << (wave_start + j) << " (" << paths[wave_start + j]
                    << "): " << read_errors[j];
            throw std::runtime_error(message.str());
          }
          native_open_s += read_timings[j].file_open_s;
          native_read_s += read_timings[j].file_read_s;
          native_bytes_read += read_timings[j].bytes_read;
        }

        double wave_elapsed_s = 0.0;
        for (std::size_t j = 0; j < frames_in_wave; ++j) {
          const std::size_t lane = j;
          const std::size_t frame_offset = wave_start + j;
          if (!lane_started[lane]) {
            check_cuda(
                cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident native path-read lane start)");
            lane_started[lane] = 1;
          }
          lane_used_in_wave[lane] = 1;
          auto* lane_raw = reinterpret_cast<unsigned char*>(d_calibration_lane_lights_[lane]);
          check_cuda(
              cudaEventRecord(calibration_lane_h2d_start_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident native path-read lane h2d start)");
          check_cuda(
              cudaMemcpyAsync(
                  lane_raw,
                  lane_host_buffers[lane].get(),
                  raw_frame_bytes,
                  cudaMemcpyHostToDevice,
                  calibration_lane_streams_[lane]),
              "cudaMemcpyAsync(resident native path-read FITS u16 light)");
          check_cuda(
              cudaEventRecord(calibration_lane_h2d_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident native path-read lane h2d done)");
          glass_calibrate_fits_u16be_bzero_f32_launch_stream(
              lane_raw,
              d_bias_,
              d_dark_,
              d_flat_,
              d_stack_ + indices[frame_offset] * pixels_per_frame_,
              pixels_per_frame_,
              has_bias_,
              has_dark_,
              has_flat_,
              params[frame_offset].master_dark_includes_bias,
              params[frame_offset].dark_scale,
              params[frame_offset].flat_floor,
              params[frame_offset].pedestal,
              calibration_lane_streams_[lane]);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_paths kernel launch");
          check_cuda(
              cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident native path-read lane calibration stop)");
        }
        const auto h2d_sync_start = Clock::now();
        for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
          if (lane_used_in_wave[lane]) {
            check_cuda(
                cudaEventSynchronize(calibration_lane_h2d_events_[lane]),
                "cudaEventSynchronize(resident native path-read lane h2d)");
          }
        }
        h2d_event_sync_s += seconds_since(h2d_sync_start);
        for (std::size_t lane = 0; lane < frames_in_wave; ++lane) {
          if (lane_used_in_wave[lane]) {
            const double lane_h2d_s = cuda_event_elapsed_s(
                calibration_lane_h2d_start_events_[lane],
                calibration_lane_h2d_events_[lane],
                "cudaEventElapsedTime(resident native path-read lane h2d)");
            wave_elapsed_s = std::max(wave_elapsed_s, lane_h2d_s);
            h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_s);
          }
        }
        wave_h2d_elapsed.push_back(wave_elapsed_s);
        ++wave_count;
      }
    } catch (...) {
      py::gil_scoped_release release;
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          cudaStreamSynchronize(calibration_lane_streams_[lane]);
        }
      }
      throw;
    }

    double sync_s = 0.0;
    {
      py::gil_scoped_release release;
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_paths synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident native path-read lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    py::list wave_h2d_elapsed_s;
    for (const double value : wave_h2d_elapsed) {
      wave_h2d_elapsed_s.append(value);
    }

    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "fits_u16be_bzero_native_path_read_calibration_batch");
    out["event_mode"] = "native_path_read_reused_stack_lane_events";
    out["timing_model"] = "native_path_read_wave_then_h2d_gpu_decode_calibration";
    out["source_sample_format"] = "fits_bitpix16_bzero32768_big_endian";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["requested_wave_frames"] = wave_frames;
    out["wave_frames"] = static_cast<unsigned long long>(effective_wave_frames);
    out["wave_frames_clamped_to_stream_count"] = wave_frames_clamped_to_stream_count;
    out["wave_count"] = static_cast<unsigned long long>(wave_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["raw_h2d_bytes"] = static_cast<unsigned long long>(raw_frame_bytes * frame_count);
    out["float32_host_bytes_avoided"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float) * frame_count);
    out["native_path_read_file_open_s"] = native_open_s;
    out["native_path_read_file_read_s"] = native_read_s;
    out["native_path_read_total_s"] = native_total_read_s;
    out["native_path_read_bytes"] = native_bytes_read;
    out["h2d_release_s"] = h2d_event_sync_s;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["callback_s"] = 0.0;
    out["callback_release_count"] = 0;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["host_release_safe"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["native_path_host_buffer_bytes"] = static_cast<unsigned long long>(raw_frame_bytes * lane_count);
    out["native_path_host_buffer_model"] = "cuda_host_alloc_portable_pinned_lane_buffers";
    out["native_path_host_buffer_pinned"] = true;
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    out["wave_h2d_elapsed_s"] = wave_h2d_elapsed_s;
    return out;
  }

  py::dict calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed(
      py::object indices_obj,
      py::object paths_obj,
      py::object data_offsets_obj,
      py::object byte_counts_obj,
      py::object light_exposures_obj,
      py::object dark_exposures_obj,
      int stream_count,
      int queue_buffer_count,
      int worker_count,
      py::object policy_obj) {
    if (pending_calibration_) {
      throw std::runtime_error("a resident calibration batch is already pending");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    if (queue_buffer_count <= 0) {
      throw std::invalid_argument("queue_buffer_count must be positive");
    }
    if (worker_count <= 0) {
      throw std::invalid_argument("worker_count must be positive");
    }
    py::dict policy;
    if (!policy_obj.is_none()) {
      policy = py::cast<py::dict>(policy_obj);
    }
    const int consumer_wave_fill_wait_us =
        dict_int(policy, "native_completion_consumer_wave_fill_wait_us", 0);
    if (consumer_wave_fill_wait_us < 0 || consumer_wave_fill_wait_us > 10000) {
      throw std::invalid_argument(
          "native_completion_consumer_wave_fill_wait_us must be between 0 and 10000");
    }
    const std::string consumer_wave_fill_mode =
        dict_string(policy, "native_completion_consumer_wave_fill_mode", "multi_wait");
    if (consumer_wave_fill_mode != "multi_wait" && consumer_wave_fill_mode != "single_wait") {
      throw std::invalid_argument(
          "native_completion_consumer_wave_fill_mode must be multi_wait or single_wait");
    }
    const std::string read_backend_policy =
        dict_string(policy, "native_completion_read_backend", "auto");
    if (read_backend_policy != "auto" &&
        read_backend_policy != "std_ifstream" &&
        read_backend_policy != "win32_sequential_scan") {
      throw std::invalid_argument(
          "native_completion_read_backend must be auto, std_ifstream, or win32_sequential_scan");
    }
    const std::string consumer_wave_fill_policy =
        consumer_wave_fill_wait_us <= 0
            ? "disabled"
            : consumer_wave_fill_mode == "single_wait"
            ? "single_wait_" + std::to_string(consumer_wave_fill_wait_us) + "us"
            : "timed_wait_" + std::to_string(consumer_wave_fill_wait_us) + "us";
    const bool consumer_wave_fill_micro_poll =
        consumer_wave_fill_wait_us > 0 && consumer_wave_fill_wait_us <= 500;
    const std::string consumer_wave_fill_wait_strategy =
        consumer_wave_fill_wait_us <= 0
            ? "disabled"
            : (consumer_wave_fill_micro_poll ? "micro_poll_yield" : "condition_variable_wait_for");
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto paths = py::cast<std::vector<std::string>>(paths_obj);
    const auto data_offsets = py::cast<std::vector<unsigned long long>>(data_offsets_obj);
    const auto byte_counts = py::cast<std::vector<unsigned long long>>(byte_counts_obj);
    const auto light_exposures = parse_float_sequence(light_exposures_obj, "light_exposures");
    const auto dark_exposures = parse_float_sequence(dark_exposures_obj, "dark_exposures");
    const std::size_t frame_count = indices.size();
    if (frame_count == 0) {
      py::dict out;
      out["schema_version"] = 1;
      out["h2d_mode"] = "fits_u16be_bzero_native_completion_calibration_batch";
      out["event_mode"] = "native_completion_queue_buffer_reuse_events";
      out["timing_model"] = "native_completion_queue_read_then_h2d_gpu_decode_calibration";
      out["source_sample_format"] = "fits_bitpix16_bzero32768_big_endian";
      out["requested_stream_count"] = stream_count;
      out["stream_count"] = 0;
      out["requested_queue_buffer_count"] = queue_buffer_count;
      out["queue_buffer_count"] = 0;
      out["requested_worker_count"] = worker_count;
      out["worker_count"] = 0;
      out["wave_count"] = 0;
      out["frame_count"] = 0;
      out["raw_h2d_bytes"] = 0;
      out["float32_host_bytes_avoided"] = 0;
      out["native_path_read_file_open_s"] = 0.0;
      out["native_path_read_file_read_s"] = 0.0;
      out["native_path_read_total_s"] = 0.0;
      out["native_path_read_bytes"] = 0;
      out["native_path_read_backend"] = "none";
      out["native_path_read_backend_policy"] = read_backend_policy;
      out["native_completion_read_file_open_s"] = 0.0;
      out["native_completion_read_file_read_s"] = 0.0;
      out["native_completion_read_total_s"] = 0.0;
      out["native_completion_read_bytes"] = 0;
      out["native_completion_read_backend"] = "none";
      out["native_completion_read_backend_policy"] = read_backend_policy;
      out["native_completion_submit_count"] = 0;
      out["native_completion_count"] = 0;
      out["native_completion_out_of_order_count"] = 0;
      out["native_completion_slot_release_mode"] = "event_query_deferred_reuse";
      out["native_completion_slot_reuse_count"] = 0;
      out["native_completion_slot_reuse_query_count"] = 0;
      out["native_completion_slot_reuse_ready_count"] = 0;
      out["native_completion_slot_reuse_wait_count"] = 0;
      out["native_completion_slot_reuse_wait_s"] = 0.0;
      out["native_completion_final_h2d_collect_count"] = 0;
      out["native_completion_consumer_schedule_mode"] = "completion_lane_wave_drain";
      out["native_completion_consumer_wave_fill_mode"] = consumer_wave_fill_mode;
      out["native_completion_consumer_wave_fill_policy"] = consumer_wave_fill_policy;
      out["native_completion_consumer_wave_fill_wait_strategy"] = consumer_wave_fill_wait_strategy;
      out["native_completion_consumer_wave_fill_wait_us"] = consumer_wave_fill_wait_us;
      out["native_completion_consumer_wave_fill_wait_count"] = 0;
      out["native_completion_consumer_wave_fill_timeout_count"] = 0;
      out["native_completion_consumer_wave_fill_wait_s"] = 0.0;
      out["native_completion_consumer_wave_count"] = 0;
      out["native_completion_consumer_max_wave_frames"] = 0;
      out["native_completion_consumer_multi_frame_wave_count"] = 0;
      out["h2d_event_sync_s"] = 0.0;
      out["h2d_event_elapsed_s"] = 0.0;
      out["stream_h2d_calibrate_store_s"] = 0.0;
      out["sync_s"] = 0.0;
      out["total_s"] = 0.0;
      out["host_release_safe"] = true;
      out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
      out["native_path_host_buffer_bytes"] = 0;
      out["native_path_host_buffer_model"] = "none";
      out["native_path_host_buffer_pinned"] = false;
      out["lane_stream_elapsed_s"] = py::list();
      out["wave_h2d_elapsed_s"] = py::list();
      out["native_completion_order_sample"] = py::list();
      return out;
    }
    if (paths.size() != frame_count ||
        data_offsets.size() != frame_count ||
        byte_counts.size() != frame_count ||
        light_exposures.size() != frame_count ||
        dark_exposures.size() != frame_count) {
      throw std::invalid_argument(
          "indices, paths, offsets, byte_counts, light_exposures, and dark_exposures must have the same length");
    }
    const std::size_t raw_frame_bytes = pixels_per_frame_ * 2u;
    for (std::size_t i = 0; i < frame_count; ++i) {
      require_index(indices[i]);
      if (byte_counts[i] != static_cast<unsigned long long>(raw_frame_bytes)) {
        throw std::invalid_argument("native completion calibration FITS byte count must equal height*width*2");
      }
    }

    const std::size_t lane_count =
        std::min<std::size_t>(static_cast<std::size_t>(stream_count), frame_count);
    const std::size_t requested_buffer_count = static_cast<std::size_t>(queue_buffer_count);
    const std::size_t minimum_buffer_count = std::min<std::size_t>(frame_count, lane_count * 2u);
    const std::size_t effective_buffer_count = std::min<std::size_t>(
        frame_count,
        std::max<std::size_t>(requested_buffer_count, minimum_buffer_count));
    const std::size_t effective_worker_count = std::min<std::size_t>(
        frame_count,
        std::max<std::size_t>(1u, static_cast<std::size_t>(worker_count)));
    ensure_calibration_lanes(lane_count);

    std::vector<std::unique_ptr<unsigned char, CudaHostUCharFree>> host_buffers;
    host_buffers.reserve(effective_buffer_count);
    for (std::size_t buffer_index = 0; buffer_index < effective_buffer_count; ++buffer_index) {
      unsigned char* buffer = nullptr;
      check_cuda(
          cudaHostAlloc(
              reinterpret_cast<void**>(&buffer),
              raw_frame_bytes,
              cudaHostAllocPortable),
          "cudaHostAlloc(resident native completion raw FITS buffer)");
      host_buffers.emplace_back(buffer);
    }
    std::vector<std::unique_ptr<CudaEvent>> buffer_h2d_start_events;
    std::vector<std::unique_ptr<CudaEvent>> buffer_h2d_done_events;
    buffer_h2d_start_events.reserve(effective_buffer_count);
    buffer_h2d_done_events.reserve(effective_buffer_count);
    for (std::size_t buffer_index = 0; buffer_index < effective_buffer_count; ++buffer_index) {
      buffer_h2d_start_events.emplace_back(
          std::make_unique<CudaEvent>("cudaEventCreate(resident native completion buffer h2d start)"));
      buffer_h2d_done_events.emplace_back(
          std::make_unique<CudaEvent>("cudaEventCreate(resident native completion buffer h2d done)"));
    }

    std::vector<CalibrationParameters> params;
    params.reserve(frame_count);
    for (std::size_t i = 0; i < frame_count; ++i) {
      py::object dark_exposure_obj = py::none();
      if (std::isfinite(dark_exposures[i]) && dark_exposures[i] > 0.0f) {
        dark_exposure_obj = py::float_(dark_exposures[i]);
      }
      params.push_back(calibration_parameters(light_exposures[i], dark_exposure_obj, policy_obj));
    }

    struct CompletionJob {
      std::size_t frame_offset = 0;
      std::size_t buffer_index = 0;
    };
    struct CompletionResult {
      std::size_t frame_offset = 0;
      std::size_t buffer_index = 0;
      RawFitsReadTiming timing;
      std::string error;
    };

    const auto total_start = Clock::now();
    std::vector<unsigned char> lane_started(lane_count, 0);
    std::vector<double> lane_elapsed(lane_count, 0.0);
    std::vector<double> h2d_elapsed_samples;
    h2d_elapsed_samples.reserve(frame_count);
    std::vector<std::size_t> completion_order_sample;
    completion_order_sample.reserve(std::min<std::size_t>(64u, frame_count));
    std::vector<unsigned char> buffer_h2d_recorded(effective_buffer_count, 0);
    std::deque<std::size_t> pending_reuse_buffers;
    double h2d_event_sync_s = 0.0;
    double h2d_event_elapsed_s = 0.0;
    double stream_s = 0.0;
    double native_open_s = 0.0;
    double native_read_s = 0.0;
    double native_total_read_s = 0.0;
    std::string native_read_backend;
    unsigned long long native_bytes_read = 0;
    unsigned long long submit_count = 0;
    unsigned long long completion_count = 0;
    unsigned long long out_of_order_count = 0;
    unsigned long long slot_reuse_count = 0;
    unsigned long long slot_reuse_query_count = 0;
    unsigned long long slot_reuse_ready_count = 0;
    unsigned long long slot_reuse_wait_count = 0;
    unsigned long long final_h2d_collect_count = 0;
    unsigned long long consumer_wave_count = 0;
    unsigned long long consumer_max_wave_frames = 0;
    unsigned long long consumer_multi_frame_wave_count = 0;
    unsigned long long consumer_wave_fill_wait_count = 0;
    unsigned long long consumer_wave_fill_timeout_count = 0;
    double consumer_wave_fill_wait_s = 0.0;
    double slot_reuse_wait_s = 0.0;

    std::mutex queue_mutex;
    std::condition_variable job_condition;
    std::condition_variable completion_condition;
    std::deque<CompletionJob> jobs;
    std::deque<CompletionResult> completions;
    bool closing = false;
    std::vector<std::thread> workers;
    workers.reserve(effective_worker_count);

    auto close_workers = [&]() {
      {
        std::lock_guard<std::mutex> lock(queue_mutex);
        closing = true;
      }
      job_condition.notify_all();
      completion_condition.notify_all();
      for (auto& worker : workers) {
        if (worker.joinable()) {
          worker.join();
        }
      }
    };

    auto submit_job = [&](std::size_t frame_offset, std::size_t buffer_index) {
      {
        std::lock_guard<std::mutex> lock(queue_mutex);
        jobs.push_back(CompletionJob{frame_offset, buffer_index});
        ++submit_count;
      }
      job_condition.notify_one();
    };

    auto collect_buffer_h2d_elapsed = [&](std::size_t buffer_index) {
      if (!buffer_h2d_recorded[buffer_index]) {
        return;
      }
      const double lane_h2d_s = cuda_event_elapsed_s(
          buffer_h2d_start_events[buffer_index]->get(),
          buffer_h2d_done_events[buffer_index]->get(),
          "cudaEventElapsedTime(resident native completion buffer h2d)");
      h2d_elapsed_samples.push_back(lane_h2d_s);
      h2d_event_elapsed_s = std::max(h2d_event_elapsed_s, lane_h2d_s);
      buffer_h2d_recorded[buffer_index] = 0;
    };

    auto try_acquire_reusable_buffer = [&](std::size_t& buffer_index) -> bool {
      for (auto it = pending_reuse_buffers.begin(); it != pending_reuse_buffers.end(); ++it) {
        const std::size_t candidate = *it;
        ++slot_reuse_query_count;
        const cudaError_t status = cudaEventQuery(buffer_h2d_done_events[candidate]->get());
        if (status == cudaSuccess) {
          ++slot_reuse_ready_count;
          buffer_index = candidate;
          pending_reuse_buffers.erase(it);
          collect_buffer_h2d_elapsed(buffer_index);
          ++slot_reuse_count;
          return true;
        }
        if (status != cudaErrorNotReady) {
          check_cuda(status, "cudaEventQuery(resident native completion reusable buffer h2d)");
        }
      }
      return false;
    };

    auto wait_for_reusable_buffer = [&]() -> std::size_t {
      if (pending_reuse_buffers.empty()) {
        throw std::runtime_error("native completion calibration has no pending buffer to reuse");
      }
      const std::size_t buffer_index = pending_reuse_buffers.front();
      pending_reuse_buffers.pop_front();
      const auto h2d_sync_start = Clock::now();
      check_cuda(
          cudaEventSynchronize(buffer_h2d_done_events[buffer_index]->get()),
          "cudaEventSynchronize(resident native completion reusable buffer h2d)");
      const double wait_s = seconds_since(h2d_sync_start);
      h2d_event_sync_s += wait_s;
      slot_reuse_wait_s += wait_s;
      ++slot_reuse_wait_count;
      collect_buffer_h2d_elapsed(buffer_index);
      ++slot_reuse_count;
      return buffer_index;
    };
    auto wait_for_wave_fill_completion = [&](std::unique_lock<std::mutex>& lock) -> bool {
      if (!consumer_wave_fill_micro_poll) {
        return completion_condition.wait_for(
            lock,
            std::chrono::microseconds(consumer_wave_fill_wait_us),
            [&]() { return closing || !completions.empty(); });
      }
      const auto deadline =
          std::chrono::steady_clock::now() + std::chrono::microseconds(consumer_wave_fill_wait_us);
      while (!closing && completions.empty() && std::chrono::steady_clock::now() < deadline) {
        lock.unlock();
        std::this_thread::yield();
        lock.lock();
      }
      return closing || !completions.empty();
    };

    try {
      py::gil_scoped_release release;
      for (std::size_t worker_index = 0; worker_index < effective_worker_count; ++worker_index) {
        workers.emplace_back([&]() {
          for (;;) {
            CompletionJob job;
            {
              std::unique_lock<std::mutex> lock(queue_mutex);
              job_condition.wait(lock, [&]() { return closing || !jobs.empty(); });
              if (jobs.empty()) {
                if (closing) {
                  break;
                }
                continue;
              }
              job = jobs.front();
              jobs.pop_front();
            }

            CompletionResult result;
            result.frame_offset = job.frame_offset;
            result.buffer_index = job.buffer_index;
            try {
              result.timing = read_raw_fits_bytes_into_ptr(
                  paths[job.frame_offset],
                  data_offsets[job.frame_offset],
                  raw_frame_bytes,
                  host_buffers[job.buffer_index].get(),
                  read_backend_policy);
            } catch (const std::exception& exc) {
              result.error = exc.what();
            } catch (...) {
              result.error = "unknown native completion calibration read error";
            }

            {
              std::lock_guard<std::mutex> lock(queue_mutex);
              completions.push_back(std::move(result));
            }
            completion_condition.notify_one();
          }
        });
      }

      std::size_t next_submit = 0;
      const std::size_t initial_submit = std::min<std::size_t>(effective_buffer_count, frame_count);
      for (; next_submit < initial_submit; ++next_submit) {
        submit_job(next_submit, next_submit);
      }

      std::size_t next_expected_completion = 0;
      std::size_t launched_count = 0;
      while (launched_count < frame_count) {
        while (next_submit < frame_count) {
          std::size_t reusable_buffer_index = 0;
          if (!try_acquire_reusable_buffer(reusable_buffer_index)) {
            break;
          }
          submit_job(next_submit, reusable_buffer_index);
          ++next_submit;
        }
        if (next_submit < frame_count && static_cast<unsigned long long>(next_submit) == completion_count) {
          const std::size_t buffer_index = wait_for_reusable_buffer();
          submit_job(next_submit, buffer_index);
          ++next_submit;
          continue;
        }
        std::vector<CompletionResult> completion_wave;
        completion_wave.reserve(lane_count);
        {
          std::unique_lock<std::mutex> lock(queue_mutex);
          completion_condition.wait(lock, [&]() { return !completions.empty(); });
          while (!completions.empty() && completion_wave.size() < lane_count) {
            completion_wave.push_back(std::move(completions.front()));
            completions.pop_front();
          }
          if (consumer_wave_fill_mode == "single_wait") {
            if (consumer_wave_fill_wait_us > 0 &&
                completion_wave.size() < lane_count &&
                submit_count > completion_count + static_cast<unsigned long long>(completion_wave.size())) {
              const auto fill_wait_start = Clock::now();
              const bool filled = wait_for_wave_fill_completion(lock);
              consumer_wave_fill_wait_s += seconds_since(fill_wait_start);
              ++consumer_wave_fill_wait_count;
              if (!filled && completions.empty()) {
                ++consumer_wave_fill_timeout_count;
              }
              while (!completions.empty() && completion_wave.size() < lane_count) {
                completion_wave.push_back(std::move(completions.front()));
                completions.pop_front();
              }
            }
          } else {
            while (consumer_wave_fill_wait_us > 0 &&
                   completion_wave.size() < lane_count &&
                   submit_count > completion_count + static_cast<unsigned long long>(completion_wave.size())) {
              const auto fill_wait_start = Clock::now();
              const bool filled = wait_for_wave_fill_completion(lock);
              consumer_wave_fill_wait_s += seconds_since(fill_wait_start);
              ++consumer_wave_fill_wait_count;
              if (!filled && completions.empty()) {
                ++consumer_wave_fill_timeout_count;
                break;
              }
              while (!completions.empty() && completion_wave.size() < lane_count) {
                completion_wave.push_back(std::move(completions.front()));
                completions.pop_front();
              }
            }
          }
        }
        if (completion_wave.empty()) {
          continue;
        }
        ++consumer_wave_count;
        consumer_max_wave_frames = std::max<unsigned long long>(
            consumer_max_wave_frames,
            static_cast<unsigned long long>(completion_wave.size()));
        if (completion_wave.size() > 1u) {
          ++consumer_multi_frame_wave_count;
        }
        for (CompletionResult& completion : completion_wave) {
          if (!completion.error.empty()) {
            std::ostringstream message;
            message << "native completion calibration read failed for frame "
                    << completion.frame_offset << " (" << paths[completion.frame_offset]
                    << "): " << completion.error;
            throw std::runtime_error(message.str());
          }
          native_open_s += completion.timing.file_open_s;
          native_read_s += completion.timing.file_read_s;
          native_total_read_s += completion.timing.total_s;
          if (native_read_backend.empty()) {
            native_read_backend = completion.timing.backend;
          } else if (native_read_backend != completion.timing.backend) {
            native_read_backend = "mixed";
          }
          native_bytes_read += completion.timing.bytes_read;
          ++completion_count;
          if (completion.frame_offset != next_expected_completion) {
            ++out_of_order_count;
          }
          ++next_expected_completion;
          if (completion_order_sample.size() < 64u) {
            completion_order_sample.push_back(completion.frame_offset);
          }

          const std::size_t lane = launched_count % lane_count;
          if (!lane_started[lane]) {
            check_cuda(
                cudaEventRecord(calibration_lane_start_events_[lane], calibration_lane_streams_[lane]),
                "cudaEventRecord(resident native completion lane start)");
            lane_started[lane] = 1;
          }
          auto* lane_raw = reinterpret_cast<unsigned char*>(d_calibration_lane_lights_[lane]);
          check_cuda(
              cudaEventRecord(
                  buffer_h2d_start_events[completion.buffer_index]->get(),
                  calibration_lane_streams_[lane]),
              "cudaEventRecord(resident native completion buffer h2d start)");
          check_cuda(
              cudaMemcpyAsync(
                  lane_raw,
                  host_buffers[completion.buffer_index].get(),
                  raw_frame_bytes,
                  cudaMemcpyHostToDevice,
                  calibration_lane_streams_[lane]),
              "cudaMemcpyAsync(resident native completion FITS u16 light)");
          check_cuda(
              cudaEventRecord(
                  buffer_h2d_done_events[completion.buffer_index]->get(),
                  calibration_lane_streams_[lane]),
              "cudaEventRecord(resident native completion buffer h2d done)");
          buffer_h2d_recorded[completion.buffer_index] = 1;
          glass_calibrate_fits_u16be_bzero_f32_launch_stream(
              lane_raw,
              d_bias_,
              d_dark_,
              d_flat_,
              d_stack_ + indices[completion.frame_offset] * pixels_per_frame_,
              pixels_per_frame_,
              has_bias_,
              has_dark_,
              has_flat_,
              params[completion.frame_offset].master_dark_includes_bias,
              params[completion.frame_offset].dark_scale,
              params[completion.frame_offset].flat_floor,
              params[completion.frame_offset].pedestal,
              calibration_lane_streams_[lane]);
          check_cuda(
              cudaGetLastError(),
              "ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_paths_completion_queue kernel launch");
          check_cuda(
              cudaEventRecord(calibration_lane_stop_events_[lane], calibration_lane_streams_[lane]),
              "cudaEventRecord(resident native completion lane calibration stop)");

          pending_reuse_buffers.push_back(completion.buffer_index);
          ++launched_count;
        }
        while (next_submit < frame_count) {
          std::size_t reusable_buffer_index = 0;
          if (!try_acquire_reusable_buffer(reusable_buffer_index)) {
            break;
          }
          submit_job(next_submit, reusable_buffer_index);
          ++next_submit;
        }
      }
      close_workers();
    } catch (...) {
      close_workers();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          cudaStreamSynchronize(calibration_lane_streams_[lane]);
        }
      }
      throw;
    }

    double sync_s = 0.0;
    {
      py::gil_scoped_release release;
      const auto sync_start = Clock::now();
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          check_cuda(
              cudaStreamSynchronize(calibration_lane_streams_[lane]),
              "ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_paths_completion_queue synchronize");
        }
      }
      sync_s = seconds_since(sync_start);
      for (std::size_t lane = 0; lane < lane_count; ++lane) {
        if (lane_started[lane]) {
          lane_elapsed[lane] = cuda_event_elapsed_s(
              calibration_lane_start_events_[lane],
              calibration_lane_stop_events_[lane],
              "cudaEventElapsedTime(resident native completion lane calibration)");
          stream_s = std::max(stream_s, lane_elapsed[lane]);
        }
      }
      for (const std::size_t buffer_index : pending_reuse_buffers) {
        collect_buffer_h2d_elapsed(buffer_index);
        ++final_h2d_collect_count;
      }
      pending_reuse_buffers.clear();
    }
    for (std::size_t index : indices) {
      mark_loaded(index);
    }
    py::list lane_stream_elapsed_s;
    for (const double value : lane_elapsed) {
      lane_stream_elapsed_s.append(value);
    }
    py::list h2d_elapsed_s;
    for (const double value : h2d_elapsed_samples) {
      h2d_elapsed_s.append(value);
    }
    py::list order_sample;
    for (const std::size_t value : completion_order_sample) {
      order_sample.append(static_cast<unsigned long long>(value));
    }

    py::dict out = calibration_timing_dict(
        ResidentCalibrationTiming{0.0, 0.0, stream_s, seconds_since(total_start)},
        "fits_u16be_bzero_native_completion_calibration_batch");
    out["event_mode"] = "native_completion_queue_buffer_reuse_events";
    out["timing_model"] = "native_completion_queue_read_then_h2d_gpu_decode_calibration";
    out["source_sample_format"] = "fits_bitpix16_bzero32768_big_endian";
    out["requested_stream_count"] = stream_count;
    out["stream_count"] = static_cast<unsigned long long>(lane_count);
    out["requested_queue_buffer_count"] = queue_buffer_count;
    out["queue_buffer_count"] = static_cast<unsigned long long>(effective_buffer_count);
    out["requested_worker_count"] = worker_count;
    out["worker_count"] = static_cast<unsigned long long>(effective_worker_count);
    out["requested_wave_frames"] = queue_buffer_count;
    out["wave_frames"] = static_cast<unsigned long long>(effective_buffer_count);
    out["wave_frames_clamped_to_stream_count"] = false;
    out["wave_count"] = static_cast<unsigned long long>(completion_count);
    out["frame_count"] = static_cast<unsigned long long>(frame_count);
    out["raw_h2d_bytes"] = static_cast<unsigned long long>(raw_frame_bytes * frame_count);
    out["float32_host_bytes_avoided"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float) * frame_count);
    out["native_path_read_file_open_s"] = native_open_s;
    out["native_path_read_file_read_s"] = native_read_s;
    out["native_path_read_total_s"] = native_total_read_s;
    out["native_path_read_bytes"] = native_bytes_read;
    out["native_path_read_backend"] = native_read_backend.empty() ? "unknown" : native_read_backend;
    out["native_path_read_backend_policy"] = read_backend_policy;
    out["native_completion_read_file_open_s"] = native_open_s;
    out["native_completion_read_file_read_s"] = native_read_s;
    out["native_completion_read_total_s"] = native_total_read_s;
    out["native_completion_read_bytes"] = native_bytes_read;
    out["native_completion_read_backend"] = native_read_backend.empty() ? "unknown" : native_read_backend;
    out["native_completion_read_backend_policy"] = read_backend_policy;
    out["native_completion_submit_count"] = submit_count;
    out["native_completion_count"] = completion_count;
    out["native_completion_out_of_order_count"] = out_of_order_count;
    out["native_completion_order_sample"] = order_sample;
    out["native_completion_slot_release_mode"] = "event_query_deferred_reuse";
    out["native_completion_slot_reuse_count"] = slot_reuse_count;
    out["native_completion_slot_reuse_query_count"] = slot_reuse_query_count;
    out["native_completion_slot_reuse_ready_count"] = slot_reuse_ready_count;
    out["native_completion_slot_reuse_wait_count"] = slot_reuse_wait_count;
    out["native_completion_slot_reuse_wait_s"] = slot_reuse_wait_s;
    out["native_completion_final_h2d_collect_count"] = final_h2d_collect_count;
    out["native_completion_consumer_schedule_mode"] = "completion_lane_wave_drain";
    out["native_completion_consumer_wave_fill_mode"] = consumer_wave_fill_mode;
    out["native_completion_consumer_wave_fill_policy"] = consumer_wave_fill_policy;
    out["native_completion_consumer_wave_fill_wait_strategy"] = consumer_wave_fill_wait_strategy;
    out["native_completion_consumer_wave_fill_wait_us"] = consumer_wave_fill_wait_us;
    out["native_completion_consumer_wave_fill_wait_count"] = consumer_wave_fill_wait_count;
    out["native_completion_consumer_wave_fill_timeout_count"] = consumer_wave_fill_timeout_count;
    out["native_completion_consumer_wave_fill_wait_s"] = consumer_wave_fill_wait_s;
    out["native_completion_consumer_wave_count"] = consumer_wave_count;
    out["native_completion_consumer_max_wave_frames"] = consumer_max_wave_frames;
    out["native_completion_consumer_multi_frame_wave_count"] = consumer_multi_frame_wave_count;
    out["h2d_release_s"] = h2d_event_sync_s;
    out["h2d_event_sync_s"] = h2d_event_sync_s;
    out["h2d_event_elapsed_s"] = h2d_event_elapsed_s;
    out["callback_s"] = 0.0;
    out["callback_release_count"] = 0;
    out["stream_h2d_calibrate_store_s"] = stream_s;
    out["sync_s"] = sync_s;
    out["host_release_safe"] = true;
    out["calibration_lane_buffer_bytes"] = calibration_lane_buffer_bytes();
    out["native_path_host_buffer_bytes"] = static_cast<unsigned long long>(raw_frame_bytes * effective_buffer_count);
    out["native_path_host_buffer_model"] = "cuda_host_alloc_portable_pinned_completion_ring";
    out["native_path_host_buffer_pinned"] = true;
    out["lane_stream_elapsed_s"] = lane_stream_elapsed_s;
    out["wave_h2d_elapsed_s"] = h2d_elapsed_s;
    return out;
  }

  void apply_translation_frame(std::size_t index, int dx, int dy, float fill) {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before translation warp");
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(false);
    allocate_warp_coverage_if_needed();
    glass_warp_translation_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        dx,
        dy,
        fill,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_translation_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident translated frame)");
    ++warp_coverage_frame_count_;
  }

  void apply_translation_bilinear_frame(std::size_t index, float dx, float dy, float fill) {
    require_loaded(index, "bilinear translation warp");
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(false);
    allocate_warp_coverage_if_needed();
    glass_warp_translation_bilinear_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        dx,
        dy,
        fill,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_translation_bilinear_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident bilinear translated frame)");
    ++warp_coverage_frame_count_;
  }

  void apply_matrix_bilinear_frame(std::size_t index, py::object matrix_obj, float fill) {
    require_loaded(index, "matrix bilinear warp");
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    allocate_warp_coverage_if_needed();
    check_cuda(
        cudaMemcpy(d_warp_inverse_, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident matrix warp inverse)");
    glass_warp_matrix_bilinear_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        d_warp_inverse_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        fill,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident matrix warped frame)");
    ++warp_coverage_frame_count_;
  }

  void apply_matrix_lanczos3_frame(
      std::size_t index,
      py::object matrix_obj,
      float fill,
      float clamping_threshold) {
    require_loaded(index, "matrix Lanczos3 warp");
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    allocate_warp_coverage_if_needed();
    check_cuda(
        cudaMemcpy(d_warp_inverse_, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(resident matrix Lanczos3 inverse)");
    glass_warp_matrix_lanczos3_f32_launch(
        d_stack_ + index * pixels_per_frame_,
        d_warp_output_,
        d_warp_frame_coverage_,
        d_warp_inverse_,
        static_cast<int>(width_),
        static_cast<int>(height_),
        fill,
        clamping_threshold,
        d_warp_coverage_);
    check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frame kernel launch");
    check_cuda(
        cudaMemcpyAsync(
            d_stack_ + index * pixels_per_frame_,
            d_warp_output_,
            frame_bytes,
            cudaMemcpyDeviceToDevice,
            0),
        "cudaMemcpyAsync(resident matrix Lanczos3 warped frame)");
    ++warp_coverage_frame_count_;
  }

  py::dict apply_matrix_bilinear_frames_loop(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      bool track_coverage = true) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "bilinear";
      result["timing_model"] = "native_loop_batched_inverse_one_sync";
      result["inverse_upload_mode"] = "single_device_batch";
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["device_copy_enqueue_s"] = 0.0;
      result["track_coverage"] = track_coverage;
      result["coverage_accumulator_updated"] = false;
      result["warp_coverage_frame_count_delta"] = 0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "loop batched matrix bilinear warp");
    }
    const auto total_start = Clock::now();
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    if (track_coverage) {
      allocate_warp_coverage_if_needed();
    }
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    for (std::size_t i = 0; i < matrices.size(); ++i) {
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);
    float* raw_inverse_batch = nullptr;
    const auto inverse_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&raw_inverse_batch, inverse_host.size() * sizeof(float)),
        "cudaMalloc(resident loop batched matrix warp inverses)");
    std::unique_ptr<float, CudaFloatFree> inverse_batch(raw_inverse_batch);
    const double inverse_alloc_s = seconds_since(inverse_alloc_start);
    const auto inverse_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            inverse_batch.get(),
            inverse_host.data(),
            inverse_host.size() * sizeof(float),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident loop batched matrix warp inverses)");
    double inverse_upload_s = seconds_since(inverse_upload_start);
    double kernel_enqueue_s = 0.0;
    double copy_enqueue_s = 0.0;
    for (std::size_t i = 0; i < indices.size(); ++i) {
      const std::size_t index = indices[i];
      const auto kernel_start = Clock::now();
      glass_warp_matrix_bilinear_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_warp_output_,
          d_warp_frame_coverage_,
          inverse_batch.get() + i * 9,
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill,
          track_coverage ? d_warp_coverage_ : nullptr);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frames_loop kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      const auto copy_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_stack_ + index * pixels_per_frame_,
              d_warp_output_,
              frame_bytes,
              cudaMemcpyDeviceToDevice,
              0),
          "cudaMemcpyAsync(resident loop batched matrix warped frame)");
      copy_enqueue_s += seconds_since(copy_start);
      if (track_coverage) {
        ++warp_coverage_frame_count_;
      }
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_bilinear_frames_loop synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "bilinear";
    result["timing_model"] = "native_loop_batched_inverse_one_sync";
    result["inverse_upload_mode"] = "single_device_batch";
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = inverse_alloc_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["device_copy_enqueue_s"] = copy_enqueue_s;
    result["track_coverage"] = track_coverage;
    result["coverage_accumulator_updated"] = track_coverage;
    result["warp_coverage_frame_count_delta"] = static_cast<unsigned long long>(
        track_coverage ? indices.size() : 0);
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_lanczos3_frames_loop(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      float clamping_threshold,
      bool track_coverage = true) {
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "lanczos3";
      result["timing_model"] = "native_loop_batched_inverse_one_sync";
      result["inverse_upload_mode"] = "single_device_batch";
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["device_copy_enqueue_s"] = 0.0;
      result["lanczos3_clamping_enabled"] = clamping_threshold >= 0.0f;
      result["track_coverage"] = track_coverage;
      result["coverage_accumulator_updated"] = false;
      result["warp_coverage_frame_count_delta"] = 0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "loop batched matrix Lanczos3 warp");
    }
    const auto total_start = Clock::now();
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    allocate_warp_scratch_if_needed(true);
    if (track_coverage) {
      allocate_warp_coverage_if_needed();
    }
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    for (std::size_t i = 0; i < matrices.size(); ++i) {
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);
    float* raw_inverse_batch = nullptr;
    const auto inverse_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&raw_inverse_batch, inverse_host.size() * sizeof(float)),
        "cudaMalloc(resident loop batched matrix Lanczos3 inverses)");
    std::unique_ptr<float, CudaFloatFree> inverse_batch(raw_inverse_batch);
    const double inverse_alloc_s = seconds_since(inverse_alloc_start);
    const auto inverse_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            inverse_batch.get(),
            inverse_host.data(),
            inverse_host.size() * sizeof(float),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident loop batched matrix Lanczos3 inverses)");
    double inverse_upload_s = seconds_since(inverse_upload_start);
    double kernel_enqueue_s = 0.0;
    double copy_enqueue_s = 0.0;
    for (std::size_t i = 0; i < indices.size(); ++i) {
      const std::size_t index = indices[i];
      const auto kernel_start = Clock::now();
      glass_warp_matrix_lanczos3_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_warp_output_,
          d_warp_frame_coverage_,
          inverse_batch.get() + i * 9,
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill,
          clamping_threshold,
          track_coverage ? d_warp_coverage_ : nullptr);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames_loop kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      const auto copy_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_stack_ + index * pixels_per_frame_,
              d_warp_output_,
              frame_bytes,
              cudaMemcpyDeviceToDevice,
              0),
          "cudaMemcpyAsync(resident loop batched matrix Lanczos3 warped frame)");
      copy_enqueue_s += seconds_since(copy_start);
      if (track_coverage) {
        ++warp_coverage_frame_count_;
      }
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames_loop synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "lanczos3";
    result["timing_model"] = "native_loop_batched_inverse_one_sync";
    result["inverse_upload_mode"] = "single_device_batch";
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = inverse_alloc_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["device_copy_enqueue_s"] = copy_enqueue_s;
    result["lanczos3_clamping_enabled"] = clamping_threshold >= 0.0f;
    result["track_coverage"] = track_coverage;
    result["coverage_accumulator_updated"] = track_coverage;
    result["warp_coverage_frame_count_delta"] = static_cast<unsigned long long>(
        track_coverage ? indices.size() : 0);
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_frames_pipelined_impl(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      float clamping_threshold,
      int max_chunk_capacity_frames,
      bool track_coverage,
      int stream_count,
      const char* interpolation) {
    if (max_chunk_capacity_frames < 0) {
      throw std::invalid_argument("max_chunk_capacity_frames must be non-negative");
    }
    if (stream_count <= 0) {
      throw std::invalid_argument("stream_count must be positive");
    }
    const std::string interpolation_name(interpolation);
    const bool lanczos3 = interpolation_name == "lanczos3";
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = interpolation_name;
      result["timing_model"] = "native_pipelined_batch_warp_serial_coverage";
      result["inverse_upload_mode"] = "pipelined_chunk_device_batch";
      result["batch_chunk_frames"] = 0;
      result["batch_chunk_count"] = 0;
      result["batch_stream_count"] = static_cast<unsigned long long>(stream_count);
      result["batch_lane_count"] = 0;
      result["batch_max_chunk_capacity_frames"] = static_cast<unsigned long long>(
          std::max(0, max_chunk_capacity_frames));
      result["batch_capacity_source"] =
          max_chunk_capacity_frames > 0 ? "explicit_max_chunk_capacity" : "native_preferred";
      result["batch_workspace_bytes"] = 0;
      result["batch_output_bytes"] = 0;
      result["batch_coverage_bytes"] = 0;
      result["chunk_metadata_upload_mode"] = "per_lane_chunk_async_metadata";
      result["index_upload_count"] = 0;
      result["inverse_upload_count"] = 0;
      result["index_upload_s"] = 0.0;
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_input_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["coverage_reduce_enqueue_s"] = 0.0;
      result["scatter_enqueue_s"] = 0.0;
      result["postprocess_enqueue_s"] = 0.0;
      result["postprocess_mode"] = track_coverage ? "serialized_fused_scatter_reduce" : "parallel_scatter_only";
      if (lanczos3) {
        result["lanczos3_clamping_enabled"] = clamping_threshold >= 0.0f;
        result["lanczos3_clamp_path"] =
            clamping_threshold >= 0.0f ? "generic_runtime_clamp" : "unclamped_specialized";
      }
      result["warp_kernel_launches"] = 0;
      result["coverage_reduce_kernel_launches"] = 0;
      result["scatter_kernel_launches"] = 0;
      result["postprocess_kernel_launches"] = 0;
      result["coverage_reduce_serialized"] = track_coverage;
      result["track_coverage"] = track_coverage;
      result["coverage_accumulator_updated"] = false;
      result["warp_coverage_frame_count_delta"] = 0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, lanczos3 ? "pipelined matrix Lanczos3 warp" : "pipelined matrix bilinear warp");
    }

    const auto total_start = Clock::now();
    if (track_coverage) {
      allocate_warp_coverage_if_needed();
    }
    std::vector<unsigned long long> index_host(indices.size(), 0ULL);
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    const auto inverse_prepare_start = Clock::now();
    for (std::size_t i = 0; i < indices.size(); ++i) {
      index_host[i] = static_cast<unsigned long long>(indices[i]);
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);

    constexpr std::size_t preferred_frames = 8;
    const std::size_t requested_capacity = std::min(
        indices.size(),
        max_chunk_capacity_frames > 0 ? static_cast<std::size_t>(max_chunk_capacity_frames) : preferred_frames);
    auto first_workspace = allocate_batch_warp_workspace(requested_capacity, requested_capacity, track_coverage);
    std::size_t chunk_capacity = first_workspace.capacity_frames;
    std::size_t planned_chunk_count = (indices.size() + chunk_capacity - 1) / chunk_capacity;
    std::size_t lane_count = std::min(
        static_cast<std::size_t>(std::max(1, stream_count)),
        std::max<std::size_t>(1, planned_chunk_count));
    std::vector<BatchWarpWorkspace> workspaces;
    workspaces.reserve(lane_count);
    workspaces.push_back(std::move(first_workspace));
    double allocation_s = workspaces[0].allocation_s;
    for (std::size_t lane = 1; lane < lane_count; ++lane) {
      auto lane_workspace = allocate_batch_warp_workspace(chunk_capacity, chunk_capacity, track_coverage);
      allocation_s += lane_workspace.allocation_s;
      chunk_capacity = std::min(chunk_capacity, lane_workspace.capacity_frames);
      workspaces.push_back(std::move(lane_workspace));
    }
    if (chunk_capacity == 0) {
      throw std::runtime_error("pipelined batch warp workspace capacity resolved to zero");
    }
    planned_chunk_count = (indices.size() + chunk_capacity - 1) / chunk_capacity;
    lane_count = std::min(lane_count, planned_chunk_count);
    std::vector<std::unique_ptr<CudaStream>> streams;
    streams.reserve(lane_count);
    for (std::size_t lane = 0; lane < lane_count; ++lane) {
      streams.push_back(std::make_unique<CudaStream>("cudaStreamCreate(resident pipelined matrix warp lane)"));
    }

    std::size_t workspace_bytes = 0;
    std::size_t output_bytes = 0;
    std::size_t coverage_bytes = 0;
    std::size_t inverse_bytes = 0;
    std::size_t index_bytes = 0;
    for (std::size_t lane = 0; lane < lane_count; ++lane) {
      workspace_bytes += workspaces[lane].output_bytes
          + workspaces[lane].coverage_bytes
          + workspaces[lane].inverse_bytes
          + workspaces[lane].index_bytes;
      output_bytes += workspaces[lane].output_bytes;
      coverage_bytes += workspaces[lane].coverage_bytes;
      inverse_bytes += workspaces[lane].inverse_bytes;
      index_bytes += workspaces[lane].index_bytes;
    }

    double index_upload_s = 0.0;
    double inverse_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double coverage_reduce_enqueue_s = 0.0;
    double scatter_enqueue_s = 0.0;
    double postprocess_enqueue_s = 0.0;
    std::size_t chunk_count = 0;
    std::size_t warp_kernel_launches = 0;
    std::size_t coverage_reduce_kernel_launches = 0;
    std::size_t scatter_kernel_launches = 0;
    std::size_t postprocess_kernel_launches = 0;
    std::vector<std::unique_ptr<CudaEvent>> postprocess_events;
    postprocess_events.reserve(planned_chunk_count);
    cudaEvent_t previous_postprocess_event = nullptr;
    const bool lanczos3_clamping_enabled = clamping_threshold >= 0.0f;

    for (std::size_t begin = 0; begin < indices.size(); begin += chunk_capacity) {
      const std::size_t chunk_frames = std::min(chunk_capacity, indices.size() - begin);
      const std::size_t lane = chunk_count % lane_count;
      auto& workspace = workspaces[lane];
      cudaStream_t stream = streams[lane]->get();

      const auto index_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              workspace.indices.get(),
              index_host.data() + begin,
              chunk_frames * sizeof(unsigned long long),
              cudaMemcpyHostToDevice,
              stream),
          "cudaMemcpyAsync(resident pipelined matrix warp chunk indices)");
      index_upload_s += seconds_since(index_upload_start);
      const auto inverse_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              workspace.inverses.get(),
              inverse_host.data() + begin * 9,
              chunk_frames * 9 * sizeof(float),
              cudaMemcpyHostToDevice,
              stream),
          "cudaMemcpyAsync(resident pipelined matrix warp chunk inverses)");
      inverse_upload_s += seconds_since(inverse_upload_start);

      const auto kernel_start = Clock::now();
      if (lanczos3) {
        if (lanczos3_clamping_enabled) {
          glass_warp_matrix_lanczos3_batch_f32_launch_stream(
              d_stack_,
              workspace.output.get(),
              workspace.coverage.get(),
              workspace.indices.get(),
              workspace.inverses.get(),
              static_cast<int>(chunk_frames),
              static_cast<int>(width_),
              static_cast<int>(height_),
              fill,
              clamping_threshold,
              stream);
        } else {
          glass_warp_matrix_lanczos3_batch_unclamped_f32_launch_stream(
              d_stack_,
              workspace.output.get(),
              workspace.coverage.get(),
              workspace.indices.get(),
              workspace.inverses.get(),
              static_cast<int>(chunk_frames),
              static_cast<int>(width_),
              static_cast<int>(height_),
              fill,
              stream);
        }
      } else {
        glass_warp_matrix_bilinear_batch_f32_launch_stream(
            d_stack_,
            workspace.output.get(),
            workspace.coverage.get(),
            workspace.indices.get(),
            workspace.inverses.get(),
            static_cast<int>(chunk_frames),
            static_cast<int>(width_),
            static_cast<int>(height_),
            fill,
            stream);
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_frames_pipelined kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      ++warp_kernel_launches;

      const auto postprocess_start = Clock::now();
      if (track_coverage) {
        if (previous_postprocess_event != nullptr) {
          check_cuda(
              cudaStreamWaitEvent(stream, previous_postprocess_event, 0),
              "cudaStreamWaitEvent(resident pipelined matrix warp coverage chain)");
        }
        glass_warp_batch_scatter_reduce_f32_launch_stream(
            workspace.output.get(),
            workspace.coverage.get(),
            d_stack_,
            d_warp_coverage_,
            workspace.indices.get(),
            static_cast<int>(chunk_frames),
            pixels_per_frame_,
            stream);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_matrix_frames_pipelined fused scatter/reduce launch");
        auto event = std::make_unique<CudaEvent>("cudaEventCreate(resident pipelined matrix warp postprocess)");
        check_cuda(
            cudaEventRecord(event->get(), stream),
            "cudaEventRecord(resident pipelined matrix warp postprocess)");
        previous_postprocess_event = event->get();
        postprocess_events.push_back(std::move(event));
        ++coverage_reduce_kernel_launches;
        warp_coverage_frame_count_ += chunk_frames;
      } else {
        glass_warp_batch_scatter_f32_launch_stream(
            workspace.output.get(),
            d_stack_,
            workspace.indices.get(),
            static_cast<int>(chunk_frames),
            pixels_per_frame_,
            stream);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_matrix_frames_pipelined scatter-only launch");
        ++scatter_kernel_launches;
      }
      postprocess_enqueue_s += seconds_since(postprocess_start);
      ++postprocess_kernel_launches;
      ++chunk_count;
    }

    const auto sync_start = Clock::now();
    for (std::size_t lane = 0; lane < lane_count; ++lane) {
      check_cuda(
          cudaStreamSynchronize(streams[lane]->get()),
          "ResidentCalibratedStack.apply_matrix_frames_pipelined synchronize lane");
    }
    const double sync_s = seconds_since(sync_start);

    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = interpolation_name;
    result["timing_model"] = "native_pipelined_batch_warp_serial_coverage";
    result["inverse_upload_mode"] = "pipelined_chunk_device_batch";
    result["batch_chunk_frames"] = static_cast<unsigned long long>(chunk_capacity);
    result["batch_chunk_count"] = static_cast<unsigned long long>(chunk_count);
    result["batch_stream_count"] = static_cast<unsigned long long>(stream_count);
    result["batch_lane_count"] = static_cast<unsigned long long>(lane_count);
    result["batch_max_chunk_capacity_frames"] = static_cast<unsigned long long>(
        std::max(0, max_chunk_capacity_frames));
    result["batch_capacity_source"] =
        max_chunk_capacity_frames > 0 ? "explicit_max_chunk_capacity" : "native_preferred";
    result["batch_workspace_bytes"] = static_cast<unsigned long long>(workspace_bytes);
    result["batch_output_bytes"] = static_cast<unsigned long long>(output_bytes);
    result["batch_coverage_bytes"] = static_cast<unsigned long long>(coverage_bytes);
    result["batch_inverse_workspace_bytes"] = static_cast<unsigned long long>(inverse_bytes);
    result["batch_index_workspace_bytes"] = static_cast<unsigned long long>(index_bytes);
    result["chunk_metadata_upload_mode"] = "per_lane_chunk_async_metadata";
    result["index_upload_count"] = static_cast<unsigned long long>(chunk_count);
    result["inverse_upload_count"] = static_cast<unsigned long long>(chunk_count);
    result["index_upload_s"] = index_upload_s;
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = allocation_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_bytes);
    result["inverse_input_bytes"] = static_cast<unsigned long long>(indices.size() * 9 * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["coverage_reduce_enqueue_s"] = coverage_reduce_enqueue_s;
    result["scatter_enqueue_s"] = scatter_enqueue_s;
    result["postprocess_enqueue_s"] = postprocess_enqueue_s;
    result["postprocess_mode"] = track_coverage ? "serialized_fused_scatter_reduce" : "parallel_scatter_only";
    if (lanczos3) {
      result["lanczos3_clamping_enabled"] = lanczos3_clamping_enabled;
      result["lanczos3_clamp_path"] =
          lanczos3_clamping_enabled ? "generic_runtime_clamp" : "unclamped_specialized";
    }
    result["warp_kernel_launches"] = static_cast<unsigned long long>(warp_kernel_launches);
    result["coverage_reduce_kernel_launches"] = static_cast<unsigned long long>(coverage_reduce_kernel_launches);
    result["scatter_kernel_launches"] = static_cast<unsigned long long>(scatter_kernel_launches);
    result["postprocess_kernel_launches"] = static_cast<unsigned long long>(postprocess_kernel_launches);
    result["coverage_reduce_serialized"] = track_coverage;
    result["track_coverage"] = track_coverage;
    result["coverage_accumulator_updated"] = track_coverage;
    result["warp_coverage_frame_count_delta"] = static_cast<unsigned long long>(
        track_coverage ? indices.size() : 0);
    result["device_copy_enqueue_s"] = postprocess_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_bilinear_frames_pipelined(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      int max_chunk_capacity_frames = 0,
      bool track_coverage = true,
      int stream_count = 2) {
    return apply_matrix_frames_pipelined_impl(
        indices_obj,
        matrices_obj,
        fill,
        -1.0f,
        max_chunk_capacity_frames,
        track_coverage,
        stream_count,
        "bilinear");
  }

  py::dict apply_matrix_lanczos3_frames_pipelined(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      float clamping_threshold,
      int max_chunk_capacity_frames = 0,
      bool track_coverage = true,
      int stream_count = 2) {
    return apply_matrix_frames_pipelined_impl(
        indices_obj,
        matrices_obj,
        fill,
        clamping_threshold,
        max_chunk_capacity_frames,
        track_coverage,
        stream_count,
        "lanczos3");
  }

  py::dict apply_matrix_bilinear_frames(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      int max_chunk_capacity_frames = 0,
      bool track_coverage = true) {
    if (max_chunk_capacity_frames < 0) {
      throw std::invalid_argument("max_chunk_capacity_frames must be non-negative");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "bilinear";
      result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
      result["inverse_upload_mode"] = "chunked_device_batch";
      result["batch_chunk_frames"] = 0;
      result["batch_chunk_count"] = 0;
      result["batch_max_chunk_capacity_frames"] = static_cast<unsigned long long>(
          std::max(0, max_chunk_capacity_frames));
      result["batch_capacity_source"] =
          max_chunk_capacity_frames > 0 ? "explicit_max_chunk_capacity" : "native_preferred";
      result["batch_workspace_bytes"] = 0;
      result["batch_output_bytes"] = 0;
      result["batch_coverage_bytes"] = 0;
      result["chunk_metadata_upload_mode"] = "single_device_batch_reused_by_chunks";
      result["index_upload_count"] = 0;
      result["inverse_upload_count"] = 0;
      result["index_upload_s"] = 0.0;
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["coverage_reduce_enqueue_s"] = 0.0;
      result["scatter_enqueue_s"] = 0.0;
      result["postprocess_enqueue_s"] = 0.0;
      result["postprocess_mode"] = track_coverage ? "fused_scatter_reduce" : "scatter_only_no_coverage_accumulator";
      result["warp_kernel_launches"] = 0;
      result["coverage_reduce_kernel_launches"] = 0;
      result["scatter_kernel_launches"] = 0;
      result["postprocess_kernel_launches"] = 0;
      result["track_coverage"] = track_coverage;
      result["coverage_accumulator_updated"] = false;
      result["warp_coverage_frame_count_delta"] = 0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "batched matrix bilinear warp");
    }
    const auto total_start = Clock::now();
    if (track_coverage) {
      allocate_warp_coverage_if_needed();
    }
    auto workspace = allocate_batch_warp_workspace(
        indices.size(),
        static_cast<std::size_t>(std::max(0, max_chunk_capacity_frames)),
        track_coverage);
    std::vector<unsigned long long> index_host(indices.size(), 0ULL);
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    const auto inverse_prepare_start = Clock::now();
    for (std::size_t i = 0; i < indices.size(); ++i) {
      index_host[i] = static_cast<unsigned long long>(indices[i]);
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);
    const auto index_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            workspace.indices.get(),
            index_host.data(),
            index_host.size() * sizeof(unsigned long long),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident batched matrix warp all indices)");
    const double index_upload_s = seconds_since(index_upload_start);
    const auto inverse_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            workspace.inverses.get(),
            inverse_host.data(),
            inverse_host.size() * sizeof(float),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident batched matrix warp all inverses)");
    const double inverse_upload_s = seconds_since(inverse_upload_start);
    double kernel_enqueue_s = 0.0;
    double coverage_reduce_enqueue_s = 0.0;
    double scatter_enqueue_s = 0.0;
    double postprocess_enqueue_s = 0.0;
    std::size_t chunk_count = 0;
    std::size_t warp_kernel_launches = 0;
    std::size_t coverage_reduce_kernel_launches = 0;
    std::size_t scatter_kernel_launches = 0;
    std::size_t postprocess_kernel_launches = 0;
    for (std::size_t begin = 0; begin < indices.size(); begin += workspace.capacity_frames) {
      const std::size_t chunk_frames = std::min(workspace.capacity_frames, indices.size() - begin);
      const auto kernel_start = Clock::now();
      glass_warp_matrix_bilinear_batch_f32_launch(
          d_stack_,
          workspace.output.get(),
          workspace.coverage.get(),
          workspace.indices.get() + begin,
          workspace.inverses.get() + begin * 9,
          static_cast<int>(chunk_frames),
          static_cast<int>(width_),
          static_cast<int>(height_),
          fill);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_bilinear_frames kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      ++warp_kernel_launches;
      const auto postprocess_start = Clock::now();
      if (track_coverage) {
        glass_warp_batch_scatter_reduce_f32_launch(
            workspace.output.get(),
            workspace.coverage.get(),
            d_stack_,
            d_warp_coverage_,
            workspace.indices.get() + begin,
            static_cast<int>(chunk_frames),
            pixels_per_frame_);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_matrix_bilinear_frames fused scatter/reduce launch");
      } else {
        glass_warp_batch_scatter_f32_launch(
            workspace.output.get(),
            d_stack_,
            workspace.indices.get() + begin,
            static_cast<int>(chunk_frames),
            pixels_per_frame_);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_matrix_bilinear_frames scatter-only launch");
        ++scatter_kernel_launches;
      }
      postprocess_enqueue_s += seconds_since(postprocess_start);
      ++postprocess_kernel_launches;
      if (track_coverage) {
        warp_coverage_frame_count_ += chunk_frames;
      }
      ++chunk_count;
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_bilinear_frames synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "bilinear";
    result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
    result["inverse_upload_mode"] = "chunked_device_batch";
    result["batch_chunk_frames"] = static_cast<unsigned long long>(workspace.capacity_frames);
    result["batch_chunk_count"] = static_cast<unsigned long long>(chunk_count);
    result["batch_max_chunk_capacity_frames"] = static_cast<unsigned long long>(
        std::max(0, max_chunk_capacity_frames));
    result["batch_capacity_source"] =
        max_chunk_capacity_frames > 0 ? "explicit_max_chunk_capacity" : "native_preferred";
    result["batch_workspace_bytes"] = static_cast<unsigned long long>(
        workspace.output_bytes + workspace.coverage_bytes + workspace.inverse_bytes + workspace.index_bytes);
    result["batch_output_bytes"] = static_cast<unsigned long long>(workspace.output_bytes);
    result["batch_coverage_bytes"] = static_cast<unsigned long long>(workspace.coverage_bytes);
    result["chunk_metadata_upload_mode"] = "single_device_batch_reused_by_chunks";
    result["index_upload_count"] = 1;
    result["inverse_upload_count"] = 1;
    result["index_upload_s"] = index_upload_s;
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = workspace.allocation_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(indices.size() * 9 * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["coverage_reduce_enqueue_s"] = coverage_reduce_enqueue_s;
    result["scatter_enqueue_s"] = scatter_enqueue_s;
    result["postprocess_enqueue_s"] = postprocess_enqueue_s;
    result["postprocess_mode"] = track_coverage ? "fused_scatter_reduce" : "scatter_only_no_coverage_accumulator";
    result["warp_kernel_launches"] = static_cast<unsigned long long>(warp_kernel_launches);
    result["coverage_reduce_kernel_launches"] = static_cast<unsigned long long>(coverage_reduce_kernel_launches);
    result["scatter_kernel_launches"] = static_cast<unsigned long long>(scatter_kernel_launches);
    result["postprocess_kernel_launches"] = static_cast<unsigned long long>(postprocess_kernel_launches);
    result["track_coverage"] = track_coverage;
    result["coverage_accumulator_updated"] = track_coverage;
    result["warp_coverage_frame_count_delta"] = static_cast<unsigned long long>(
        track_coverage ? indices.size() : 0);
    result["device_copy_enqueue_s"] = postprocess_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_matrix_lanczos3_frames(
      py::object indices_obj,
      py::object matrices_obj,
      float fill,
      float clamping_threshold,
      int max_chunk_capacity_frames = 0,
      bool track_coverage = true) {
    if (max_chunk_capacity_frames < 0) {
      throw std::invalid_argument("max_chunk_capacity_frames must be non-negative");
    }
    const auto indices = parse_index_sequence(indices_obj, "indices");
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (indices.size() != matrices.size()) {
      throw std::invalid_argument("indices and matrices must have the same length");
    }
    if (indices.empty()) {
      py::dict result;
      result["schema_version"] = 1;
      result["frame_count"] = 0;
      result["interpolation"] = "lanczos3";
      result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
      result["inverse_upload_mode"] = "chunked_device_batch";
      result["batch_chunk_frames"] = 0;
      result["batch_chunk_count"] = 0;
      result["batch_max_chunk_capacity_frames"] = static_cast<unsigned long long>(
          std::max(0, max_chunk_capacity_frames));
      result["batch_capacity_source"] =
          max_chunk_capacity_frames > 0 ? "explicit_max_chunk_capacity" : "native_preferred";
      result["batch_workspace_bytes"] = 0;
      result["batch_output_bytes"] = 0;
      result["batch_coverage_bytes"] = 0;
      result["chunk_metadata_upload_mode"] = "single_device_batch_reused_by_chunks";
      result["index_upload_count"] = 0;
      result["inverse_upload_count"] = 0;
      result["index_upload_s"] = 0.0;
      result["inverse_prepare_s"] = 0.0;
      result["inverse_batch_alloc_s"] = 0.0;
      result["inverse_batch_bytes"] = 0;
      result["inverse_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["coverage_reduce_enqueue_s"] = 0.0;
      result["scatter_enqueue_s"] = 0.0;
      result["postprocess_enqueue_s"] = 0.0;
      result["postprocess_mode"] = track_coverage ? "fused_scatter_reduce" : "scatter_only_no_coverage_accumulator";
      result["lanczos3_clamping_enabled"] = clamping_threshold >= 0.0f;
      result["lanczos3_clamp_path"] =
          clamping_threshold >= 0.0f ? "generic_runtime_clamp" : "unclamped_specialized";
      result["warp_kernel_launches"] = 0;
      result["coverage_reduce_kernel_launches"] = 0;
      result["scatter_kernel_launches"] = 0;
      result["postprocess_kernel_launches"] = 0;
      result["track_coverage"] = track_coverage;
      result["coverage_accumulator_updated"] = false;
      result["warp_coverage_frame_count_delta"] = 0;
      result["device_copy_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      return result;
    }
    for (const std::size_t index : indices) {
      require_loaded(index, "batched matrix Lanczos3 warp");
    }
    const auto total_start = Clock::now();
    if (track_coverage) {
      allocate_warp_coverage_if_needed();
    }
    auto workspace = allocate_batch_warp_workspace(
        indices.size(),
        static_cast<std::size_t>(std::max(0, max_chunk_capacity_frames)),
        track_coverage);
    std::vector<unsigned long long> index_host(indices.size(), 0ULL);
    std::vector<float> inverse_host(indices.size() * 9, 0.0f);
    const auto inverse_prepare_start = Clock::now();
    for (std::size_t i = 0; i < indices.size(); ++i) {
      index_host[i] = static_cast<unsigned long long>(indices[i]);
      const auto inverse = invert_matrix3x3(matrices[i]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(i * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);
    const auto index_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            workspace.indices.get(),
            index_host.data(),
            index_host.size() * sizeof(unsigned long long),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident batched matrix Lanczos3 all indices)");
    const double index_upload_s = seconds_since(index_upload_start);
    const auto inverse_upload_start = Clock::now();
    check_cuda(
        cudaMemcpyAsync(
            workspace.inverses.get(),
            inverse_host.data(),
            inverse_host.size() * sizeof(float),
            cudaMemcpyHostToDevice,
            0),
        "cudaMemcpyAsync(resident batched matrix Lanczos3 all inverses)");
    const double inverse_upload_s = seconds_since(inverse_upload_start);
    double kernel_enqueue_s = 0.0;
    double coverage_reduce_enqueue_s = 0.0;
    double scatter_enqueue_s = 0.0;
    double postprocess_enqueue_s = 0.0;
    std::size_t chunk_count = 0;
    std::size_t warp_kernel_launches = 0;
    std::size_t coverage_reduce_kernel_launches = 0;
    std::size_t scatter_kernel_launches = 0;
    std::size_t postprocess_kernel_launches = 0;
    const bool lanczos3_clamping_enabled = clamping_threshold >= 0.0f;
    for (std::size_t begin = 0; begin < indices.size(); begin += workspace.capacity_frames) {
      const std::size_t chunk_frames = std::min(workspace.capacity_frames, indices.size() - begin);
      const auto kernel_start = Clock::now();
      if (lanczos3_clamping_enabled) {
        glass_warp_matrix_lanczos3_batch_f32_launch(
            d_stack_,
            workspace.output.get(),
            workspace.coverage.get(),
            workspace.indices.get() + begin,
            workspace.inverses.get() + begin * 9,
            static_cast<int>(chunk_frames),
            static_cast<int>(width_),
            static_cast<int>(height_),
            fill,
            clamping_threshold);
      } else {
        glass_warp_matrix_lanczos3_batch_unclamped_f32_launch(
            d_stack_,
            workspace.output.get(),
            workspace.coverage.get(),
            workspace.indices.get() + begin,
            workspace.inverses.get() + begin * 9,
            static_cast<int>(chunk_frames),
            static_cast<int>(width_),
            static_cast<int>(height_),
            fill);
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames kernel launch");
      kernel_enqueue_s += seconds_since(kernel_start);
      ++warp_kernel_launches;
      const auto postprocess_start = Clock::now();
      if (track_coverage) {
        glass_warp_batch_scatter_reduce_f32_launch(
            workspace.output.get(),
            workspace.coverage.get(),
            d_stack_,
            d_warp_coverage_,
            workspace.indices.get() + begin,
            static_cast<int>(chunk_frames),
            pixels_per_frame_);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_matrix_lanczos3_frames fused scatter/reduce launch");
      } else {
        glass_warp_batch_scatter_f32_launch(
            workspace.output.get(),
            d_stack_,
            workspace.indices.get() + begin,
            static_cast<int>(chunk_frames),
            pixels_per_frame_);
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.apply_matrix_lanczos3_frames scatter-only launch");
        ++scatter_kernel_launches;
      }
      postprocess_enqueue_s += seconds_since(postprocess_start);
      ++postprocess_kernel_launches;
      if (track_coverage) {
        warp_coverage_frame_count_ += chunk_frames;
      }
      ++chunk_count;
    }
    const auto sync_start = Clock::now();
    check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_matrix_lanczos3_frames synchronize");
    const double sync_s = seconds_since(sync_start);
    py::dict result;
    result["schema_version"] = 1;
    result["frame_count"] = static_cast<unsigned long long>(indices.size());
    result["interpolation"] = "lanczos3";
    result["timing_model"] = "native_chunked_batch_warp_scatter_one_sync";
    result["inverse_upload_mode"] = "chunked_device_batch";
    result["batch_chunk_frames"] = static_cast<unsigned long long>(workspace.capacity_frames);
    result["batch_chunk_count"] = static_cast<unsigned long long>(chunk_count);
    result["batch_max_chunk_capacity_frames"] = static_cast<unsigned long long>(
        std::max(0, max_chunk_capacity_frames));
    result["batch_capacity_source"] =
        max_chunk_capacity_frames > 0 ? "explicit_max_chunk_capacity" : "native_preferred";
    result["batch_workspace_bytes"] = static_cast<unsigned long long>(
        workspace.output_bytes + workspace.coverage_bytes + workspace.inverse_bytes + workspace.index_bytes);
    result["batch_output_bytes"] = static_cast<unsigned long long>(workspace.output_bytes);
    result["batch_coverage_bytes"] = static_cast<unsigned long long>(workspace.coverage_bytes);
    result["chunk_metadata_upload_mode"] = "single_device_batch_reused_by_chunks";
    result["index_upload_count"] = 1;
    result["inverse_upload_count"] = 1;
    result["index_upload_s"] = index_upload_s;
    result["inverse_prepare_s"] = inverse_prepare_s;
    result["inverse_batch_alloc_s"] = workspace.allocation_s;
    result["inverse_batch_bytes"] = static_cast<unsigned long long>(indices.size() * 9 * sizeof(float));
    result["inverse_upload_s"] = inverse_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["coverage_reduce_enqueue_s"] = coverage_reduce_enqueue_s;
    result["scatter_enqueue_s"] = scatter_enqueue_s;
    result["postprocess_enqueue_s"] = postprocess_enqueue_s;
    result["postprocess_mode"] = track_coverage ? "fused_scatter_reduce" : "scatter_only_no_coverage_accumulator";
    result["lanczos3_clamping_enabled"] = lanczos3_clamping_enabled;
    result["lanczos3_clamp_path"] =
        lanczos3_clamping_enabled ? "generic_runtime_clamp" : "unclamped_specialized";
    result["warp_kernel_launches"] = static_cast<unsigned long long>(warp_kernel_launches);
    result["coverage_reduce_kernel_launches"] = static_cast<unsigned long long>(coverage_reduce_kernel_launches);
    result["scatter_kernel_launches"] = static_cast<unsigned long long>(scatter_kernel_launches);
    result["postprocess_kernel_launches"] = static_cast<unsigned long long>(postprocess_kernel_launches);
    result["track_coverage"] = track_coverage;
    result["coverage_accumulator_updated"] = track_coverage;
    result["warp_coverage_frame_count_delta"] = static_cast<unsigned long long>(
        track_coverage ? indices.size() : 0);
    result["device_copy_enqueue_s"] = postprocess_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict matrix_alignment_metrics_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      py::object matrix_obj,
      int sample_stride) const {
    require_loaded(reference_index, "resident matrix alignment metrics");
    require_loaded(moving_index, "resident matrix alignment metrics");
    if (sample_stride <= 0) {
      throw std::invalid_argument("sample_stride must be positive");
    }
    const int stride = sample_stride > 1 ? sample_stride : 1;
    const int sample_width = static_cast<int>((width_ + static_cast<std::size_t>(stride) - 1) / static_cast<std::size_t>(stride));
    const int sample_height = static_cast<int>((height_ + static_cast<std::size_t>(stride) - 1) / static_cast<std::size_t>(stride));
    const int sampled_pixels = sample_width * sample_height;
    constexpr int threads = 256;
    const int blocks = std::max(1, std::min(1024, (sampled_pixels + threads - 1) / threads));
    const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
    std::vector<double> partial_stats(static_cast<std::size_t>(blocks) * 7, 0.0);
    std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);
    float* d_inverse = nullptr;
    double* d_partial_stats = nullptr;
    unsigned long long* d_partial_count = nullptr;
    try {
      check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(resident matrix metrics inverse)");
      check_cuda(
          cudaMalloc(&d_partial_stats, partial_stats.size() * sizeof(double)),
          "cudaMalloc(resident matrix metrics partial stats)");
      check_cuda(
          cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident matrix metrics partial count)");
      check_cuda(
          cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident matrix metrics inverse)");
      glass_matrix_alignment_metrics_f32_launch(
          d_stack_ + reference_index * pixels_per_frame_,
          d_stack_ + moving_index * pixels_per_frame_,
          d_inverse,
          d_partial_stats,
          d_partial_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          stride,
          blocks);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.matrix_alignment_metrics_to_reference kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.matrix_alignment_metrics_to_reference synchronize");
      check_cuda(
          cudaMemcpy(partial_stats.data(), d_partial_stats, partial_stats.size() * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident matrix metrics partial stats)");
      check_cuda(
          cudaMemcpy(
              partial_count.data(),
              d_partial_count,
              partial_count.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident matrix metrics partial count)");
    } catch (...) {
      cudaFree(d_inverse);
      cudaFree(d_partial_stats);
      cudaFree(d_partial_count);
      throw;
    }
    cudaFree(d_inverse);
    cudaFree(d_partial_stats);
    cudaFree(d_partial_count);

    double sum_ref = 0.0;
    double sum_mov = 0.0;
    double sum_ref2 = 0.0;
    double sum_mov2 = 0.0;
    double sum_cross = 0.0;
    double sum_diff2 = 0.0;
    double sum_abs_diff = 0.0;
    unsigned long long valid_pixels = 0ULL;
    for (int block = 0; block < blocks; ++block) {
      const std::size_t offset = static_cast<std::size_t>(block) * 7;
      sum_ref += partial_stats[offset + 0];
      sum_mov += partial_stats[offset + 1];
      sum_ref2 += partial_stats[offset + 2];
      sum_mov2 += partial_stats[offset + 3];
      sum_cross += partial_stats[offset + 4];
      sum_diff2 += partial_stats[offset + 5];
      sum_abs_diff += partial_stats[offset + 6];
      valid_pixels += partial_count[static_cast<std::size_t>(block)];
    }

    const double count = static_cast<double>(valid_pixels);
    double rms = std::numeric_limits<double>::quiet_NaN();
    double mean_abs_diff = std::numeric_limits<double>::quiet_NaN();
    double ncc = std::numeric_limits<double>::quiet_NaN();
    if (valid_pixels > 0ULL) {
      rms = std::sqrt(sum_diff2 / count);
      mean_abs_diff = sum_abs_diff / count;
    }
    if (valid_pixels > 1ULL) {
      const double numerator = sum_cross - (sum_ref * sum_mov / count);
      const double ref_var = std::max(sum_ref2 - (sum_ref * sum_ref / count), 0.0);
      const double mov_var = std::max(sum_mov2 - (sum_mov * sum_mov / count), 0.0);
      const double denominator = std::sqrt(ref_var * mov_var);
      if (denominator > 0.0) {
        ncc = numerator / denominator;
      }
    }

    py::dict result;
    result["valid_pixels"] = valid_pixels;
    result["sampled_pixels"] = sampled_pixels;
    result["sample_stride"] = stride;
    result["rms"] = rms;
    result["mean_abs_diff"] = mean_abs_diff;
    result["ncc"] = ncc;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_matrix_alignment_metrics_cuda";
    return result;
  }

  py::dict star_core_metrics_candidates_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      py::object matrices_obj,
      float threshold) const {
    require_loaded(reference_index, "resident star core candidate metrics");
    require_loaded(moving_index, "resident star core candidate metrics");
    const auto matrices = parse_matrix_stack(matrices_obj);
    const auto* d_reference = d_stack_ + reference_index * pixels_per_frame_;
    const auto* d_moving = d_stack_ + moving_index * pixels_per_frame_;
    const auto metrics = score_star_core_matrix_candidates_f32(
        d_reference,
        d_moving,
        matrices,
        static_cast<int>(width_),
        static_cast<int>(height_),
        threshold);

    py::list candidate_metrics;
    for (std::size_t index = 0; index < metrics.size(); ++index) {
      py::dict item;
      item["seed_index"] = static_cast<int>(index);
      item["metrics"] = matrix_candidate_to_dict(
          metrics[index],
          "resident_star_core_bilinear_metric_cuda_candidate");
      candidate_metrics.append(item);
    }

    py::dict result;
    result["candidate_count"] = static_cast<int>(metrics.size());
    result["threshold"] = threshold;
    result["sampled_pixels"] = static_cast<unsigned long long>(pixels_per_frame_);
    result["candidate_metrics"] = candidate_metrics;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_star_core_bilinear_metric_cuda";
    return result;
  }

  py::dict refine_matrix_translation_candidates_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      py::object matrices_obj,
      float search_radius_px,
      float coarse_step_px,
      float fine_radius_px,
      float fine_step_px,
      int coarse_sample_stride,
      int final_sample_stride) const {
    require_loaded(reference_index, "resident matrix multi-refine");
    require_loaded(moving_index, "resident matrix multi-refine");
    if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
      throw std::invalid_argument("search radii must be non-negative");
    }
    if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
      throw std::invalid_argument("search steps must be positive");
    }
    if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
      throw std::invalid_argument("sample strides must be positive");
    }
    const auto seed_matrices = parse_matrix_stack(matrices_obj);
    const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
    const int coarse_candidates = static_cast<int>(coarse_offsets.size());
    const auto* d_reference = d_stack_ + reference_index * pixels_per_frame_;
    const auto* d_moving = d_stack_ + moving_index * pixels_per_frame_;
    MatrixCandidateMetrics best;
    bool have_best = false;
    int selected_index = -1;
    py::list seed_results;

    for (std::size_t seed_index = 0; seed_index < seed_matrices.size(); ++seed_index) {
      const auto& base_matrix = seed_matrices[seed_index];
      const MatrixCandidateMetrics coarse_best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          coarse_offsets,
          static_cast<int>(width_),
          static_cast<int>(height_),
          coarse_sample_stride);
      MatrixCandidateMetrics seed_best = coarse_best;
      int fine_candidates = 0;
      if (fine_radius_px > 0.0f) {
        const auto fine_offsets = translation_offsets(coarse_best.dx, coarse_best.dy, fine_radius_px, fine_step_px);
        fine_candidates = static_cast<int>(fine_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            fine_offsets,
            static_cast<int>(width_),
            static_cast<int>(height_),
            final_sample_stride);
      } else if (final_sample_stride != coarse_sample_stride) {
        const std::vector<std::pair<float, float>> final_offsets{{coarse_best.dx, coarse_best.dy}};
        fine_candidates = static_cast<int>(final_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            final_offsets,
            static_cast<int>(width_),
            static_cast<int>(height_),
            final_sample_stride);
      }

      py::dict seed_result;
      seed_result["seed_index"] = static_cast<int>(seed_index);
      seed_result["matrix"] = matrix3x3_to_pylist(seed_best.matrix);
      seed_result["dx_correction"] = seed_best.dx;
      seed_result["dy_correction"] = seed_best.dy;
      seed_result["metrics"] = matrix_candidate_to_dict(seed_best, "matrix_alignment_metrics_cuda_candidate_grid");
      seed_result["coarse_candidates"] = coarse_candidates;
      seed_result["fine_candidates"] = fine_candidates;
      seed_results.append(seed_result);

      if (!have_best || better_matrix_metric(seed_best, best)) {
        best = seed_best;
        selected_index = static_cast<int>(seed_index);
        have_best = true;
      }
    }
    if (!have_best) {
      throw std::runtime_error("resident matrix multi-refine produced no candidates");
    }
    py::dict result;
    result["matrix"] = matrix3x3_to_pylist(best.matrix);
    result["dx_correction"] = best.dx;
    result["dy_correction"] = best.dy;
    result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
    result["selected_index"] = selected_index;
    result["seed_count"] = static_cast<int>(seed_matrices.size());
    result["seed_results"] = seed_results;
    result["coarse_candidates_per_seed"] = coarse_candidates;
    result["search_radius_px"] = search_radius_px;
    result["coarse_step_px"] = coarse_step_px;
    result["fine_radius_px"] = fine_radius_px;
    result["fine_step_px"] = fine_step_px;
    result["coarse_sample_stride"] = coarse_sample_stride;
    result["final_sample_stride"] = final_sample_stride;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_cuda_matrix_metric_translation_multi_seed_refine_grid";
    return result;
  }

  py::list refine_matrix_translation_candidates_batch_to_reference(
      std::size_t reference_index,
      const std::vector<std::size_t>& moving_indices,
      py::object matrices_obj,
      float search_radius_px,
      float coarse_step_px,
      float fine_radius_px,
      float fine_step_px,
      int coarse_sample_stride,
      int final_sample_stride) const {
    require_loaded(reference_index, "resident matrix batch refine");
    if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
      throw std::invalid_argument("search radii must be non-negative");
    }
    if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
      throw std::invalid_argument("search steps must be positive");
    }
    if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
      throw std::invalid_argument("sample strides must be positive");
    }
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (moving_indices.empty()) {
      return py::list();
    }
    if (matrices.size() != moving_indices.size()) {
      throw std::invalid_argument("batch refine requires one seed matrix per moving frame");
    }
    for (const auto moving_index : moving_indices) {
      require_loaded(moving_index, "resident matrix batch refine");
    }
    const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
    const int coarse_candidates = static_cast<int>(coarse_offsets.size());
    const int fine_candidate_capacity =
        fine_radius_px > 0.0f ? static_cast<int>(translation_offsets(0.0f, 0.0f, fine_radius_px, fine_step_px).size())
                              : final_sample_stride != coarse_sample_stride ? 1
                                                                            : 0;
    const std::size_t moving_count = moving_indices.size();
    const std::size_t coarse_total_candidate_capacity =
        moving_count * static_cast<std::size_t>(coarse_candidates);
    const std::size_t fine_total_candidate_capacity =
        moving_count * static_cast<std::size_t>(fine_candidate_capacity);
    const std::size_t workspace_candidate_capacity_size =
        std::max(coarse_total_candidate_capacity, fine_total_candidate_capacity);
    if (workspace_candidate_capacity_size > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("too many resident matrix refine candidates for one native batch");
    }
    const int workspace_candidate_capacity = static_cast<int>(workspace_candidate_capacity_size);
    const std::size_t workspace_bytes = matrix_refine_workspace_bytes(workspace_candidate_capacity);
    const auto* d_reference = d_stack_ + reference_index * pixels_per_frame_;
    py::list results;
    MatrixRefineWorkspace workspace;
    workspace.candidate_capacity = workspace_candidate_capacity;
    double native_coarse_total_s = 0.0;
    double native_fine_total_s = 0.0;

    try {
      check_cuda(
          cudaMalloc(
              &workspace.d_inverses,
              static_cast<std::size_t>(workspace_candidate_capacity) * 9 * sizeof(float)),
          "cudaMalloc(resident batch matrix refine candidate inverses)");
      check_cuda(
          cudaMalloc(
              &workspace.d_partial_stats,
              static_cast<std::size_t>(workspace_candidate_capacity) * 7 * sizeof(double)),
          "cudaMalloc(resident batch matrix refine partial stats)");
      check_cuda(
          cudaMalloc(
              &workspace.d_partial_count,
              static_cast<std::size_t>(workspace_candidate_capacity) * sizeof(unsigned long long)),
          "cudaMalloc(resident batch matrix refine partial count)");
      check_cuda(
          cudaMalloc(
              &workspace.d_moving_frame_indices,
              static_cast<std::size_t>(workspace_candidate_capacity) * sizeof(int)),
          "cudaMalloc(resident batch matrix refine moving frame indices)");
    } catch (...) {
      cudaFree(workspace.d_inverses);
      cudaFree(workspace.d_partial_stats);
      cudaFree(workspace.d_partial_count);
      cudaFree(workspace.d_moving_frame_indices);
      throw;
    }
    try {
      const std::vector<std::vector<std::pair<float, float>>> coarse_offsets_by_frame(moving_count, coarse_offsets);
      const auto coarse_start = Clock::now();
      const auto coarse_bests = score_matrix_translation_candidates_batch_f32_workspace(
          d_reference,
          d_stack_,
          pixels_per_frame_,
          moving_indices,
          matrices,
          coarse_offsets_by_frame,
          static_cast<int>(width_),
          static_cast<int>(height_),
          coarse_sample_stride,
          workspace);
      native_coarse_total_s = seconds_since(coarse_start);

      std::vector<std::vector<std::pair<float, float>>> fine_offsets_by_frame(moving_count);
      std::vector<int> fine_candidate_counts(moving_count, 0);
      bool run_fine_metric = false;
      for (std::size_t batch_index = 0; batch_index < moving_indices.size(); ++batch_index) {
        if (fine_radius_px > 0.0f) {
          fine_offsets_by_frame[batch_index] =
              translation_offsets(coarse_bests[batch_index].dx, coarse_bests[batch_index].dy, fine_radius_px, fine_step_px);
          run_fine_metric = true;
        } else if (final_sample_stride != coarse_sample_stride) {
          fine_offsets_by_frame[batch_index] = {{coarse_bests[batch_index].dx, coarse_bests[batch_index].dy}};
          run_fine_metric = true;
        }
        fine_candidate_counts[batch_index] = static_cast<int>(fine_offsets_by_frame[batch_index].size());
      }

      std::vector<MatrixCandidateMetrics> bests = coarse_bests;
      int fine_total_candidates = 0;
      for (const int count : fine_candidate_counts) {
        fine_total_candidates += count;
      }
      if (run_fine_metric) {
        const auto fine_start = Clock::now();
        bests = score_matrix_translation_candidates_batch_f32_workspace(
            d_reference,
            d_stack_,
            pixels_per_frame_,
            moving_indices,
            matrices,
            fine_offsets_by_frame,
            static_cast<int>(width_),
            static_cast<int>(height_),
            final_sample_stride,
            workspace);
        native_fine_total_s = seconds_since(fine_start);
      }

      const double per_frame_coarse_s = native_coarse_total_s / static_cast<double>(moving_count);
      const double per_frame_fine_s =
          run_fine_metric ? native_fine_total_s / static_cast<double>(moving_count) : 0.0;
      const int batch_metric_kernel_launches = run_fine_metric ? 2 : 1;
      const int coarse_total_candidates = static_cast<int>(coarse_total_candidate_capacity);
      const int coarse_stride = coarse_sample_stride > 1 ? coarse_sample_stride : 1;
      const int fine_stride = final_sample_stride > 1 ? final_sample_stride : 1;
      const unsigned long long coarse_sampled_pixels_per_candidate =
          static_cast<unsigned long long>((width_ + coarse_stride - 1) / coarse_stride) *
          static_cast<unsigned long long>((height_ + coarse_stride - 1) / coarse_stride);
      const unsigned long long fine_sampled_pixels_per_candidate =
          static_cast<unsigned long long>((width_ + fine_stride - 1) / fine_stride) *
          static_cast<unsigned long long>((height_ + fine_stride - 1) / fine_stride);
      const unsigned long long coarse_metric_sample_evaluations =
          static_cast<unsigned long long>(coarse_total_candidates) * coarse_sampled_pixels_per_candidate;
      const unsigned long long fine_metric_sample_evaluations =
          static_cast<unsigned long long>(fine_total_candidates) * fine_sampled_pixels_per_candidate;
      const double coarse_metric_megasamples_per_s =
          native_coarse_total_s > 0.0
              ? static_cast<double>(coarse_metric_sample_evaluations) / (native_coarse_total_s * 1.0e6)
              : 0.0;
      const double fine_metric_megasamples_per_s =
          native_fine_total_s > 0.0
              ? static_cast<double>(fine_metric_sample_evaluations) / (native_fine_total_s * 1.0e6)
              : 0.0;

      for (std::size_t batch_index = 0; batch_index < moving_indices.size(); ++batch_index) {
        const std::size_t moving_index = moving_indices[batch_index];
        const MatrixCandidateMetrics& best = bests[batch_index];
        const int fine_candidates = fine_candidate_counts[batch_index];
        py::dict seed_result;
        seed_result["seed_index"] = 0;
        seed_result["matrix"] = matrix3x3_to_pylist(best.matrix);
        seed_result["dx_correction"] = best.dx;
        seed_result["dy_correction"] = best.dy;
        seed_result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
        seed_result["coarse_candidates"] = coarse_candidates;
        seed_result["fine_candidates"] = fine_candidates;

        py::list seed_results;
        seed_results.append(seed_result);

        py::dict result;
        result["matrix"] = matrix3x3_to_pylist(best.matrix);
        result["dx_correction"] = best.dx;
        result["dy_correction"] = best.dy;
        result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
        result["selected_index"] = 0;
        result["seed_count"] = 1;
        result["seed_results"] = seed_results;
        result["coarse_candidates_per_seed"] = coarse_candidates;
        result["search_radius_px"] = search_radius_px;
        result["coarse_step_px"] = coarse_step_px;
        result["fine_radius_px"] = fine_radius_px;
        result["fine_step_px"] = fine_step_px;
        result["coarse_sample_stride"] = coarse_sample_stride;
        result["final_sample_stride"] = final_sample_stride;
        result["reference_index"] = reference_index;
        result["moving_index"] = moving_index;
        result["batch_index"] = static_cast<int>(batch_index);
        result["batch_count"] = static_cast<int>(moving_indices.size());
        result["batch_model"] = "resident_cuda_matrix_metric_translation_batch_refine_grid";
        result["batch_metric_mode"] = "flattened_frame_candidate_grid";
        result["batch_metric_kernel_launches"] = batch_metric_kernel_launches;
        result["metric_workload_model"] = "candidate_count_x_sampled_pixels";
        result["coarse_total_candidates"] = coarse_total_candidates;
        result["fine_total_candidates"] = fine_total_candidates;
        result["coarse_sampled_pixels_per_candidate"] = coarse_sampled_pixels_per_candidate;
        result["fine_sampled_pixels_per_candidate"] = fine_sampled_pixels_per_candidate;
        result["coarse_metric_sample_evaluations"] = coarse_metric_sample_evaluations;
        result["fine_metric_sample_evaluations"] = fine_metric_sample_evaluations;
        result["coarse_metric_megasamples_per_s"] = coarse_metric_megasamples_per_s;
        result["fine_metric_megasamples_per_s"] = fine_metric_megasamples_per_s;
        result["workspace_mode"] = "shared_flattened_candidate_metric_buffers";
        result["workspace_candidate_capacity"] = workspace_candidate_capacity;
        result["workspace_bytes"] = static_cast<unsigned long long>(workspace_bytes);
        result["coarse_metric_s"] = per_frame_coarse_s;
        result["fine_metric_s"] = per_frame_fine_s;
        result["native_coarse_total_s"] = native_coarse_total_s;
        result["native_fine_total_s"] = native_fine_total_s;
        result["model"] = "resident_cuda_matrix_metric_translation_multi_seed_refine_grid";
        results.append(result);
      }
    } catch (...) {
      cudaFree(workspace.d_inverses);
      cudaFree(workspace.d_partial_stats);
      cudaFree(workspace.d_partial_count);
      cudaFree(workspace.d_moving_frame_indices);
      throw;
    }
    cudaFree(workspace.d_inverses);
    cudaFree(workspace.d_partial_stats);
    cudaFree(workspace.d_partial_count);
    cudaFree(workspace.d_moving_frame_indices);
    return results;
  }

  py::dict estimate_translation_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      int max_shift_x,
      int max_shift_y,
      int sample_stride) const {
    require_loaded(reference_index, "resident translation search");
    require_loaded(moving_index, "resident translation search");
    if (max_shift_x < 0 || max_shift_y < 0) {
      throw std::invalid_argument("max shifts must be non-negative");
    }
    if (sample_stride <= 0) {
      throw std::invalid_argument("sample_stride must be positive");
    }
    const int shift_count = (2 * max_shift_x + 1) * (2 * max_shift_y + 1);
    float* d_scores = nullptr;
    int* d_best_dx = nullptr;
    int* d_best_dy = nullptr;
    float* d_best_score = nullptr;
    int best_dx = 0;
    int best_dy = 0;
    float best_score = 0.0f;
    try {
      check_cuda(cudaMalloc(&d_scores, static_cast<std::size_t>(shift_count) * sizeof(float)), "cudaMalloc(resident translation scores)");
      check_cuda(cudaMalloc(&d_best_dx, sizeof(int)), "cudaMalloc(resident translation best dx)");
      check_cuda(cudaMalloc(&d_best_dy, sizeof(int)), "cudaMalloc(resident translation best dy)");
      check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(resident translation best score)");
      glass_estimate_translation_search_f32_launch(
          d_stack_ + reference_index * pixels_per_frame_,
          d_stack_ + moving_index * pixels_per_frame_,
          d_scores,
          d_best_dx,
          d_best_dy,
          d_best_score,
          static_cast<int>(width_),
          static_cast<int>(height_),
          max_shift_x,
          max_shift_y,
          sample_stride);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.estimate_translation_to_reference kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.estimate_translation_to_reference synchronize");
      check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident best dx)");
      check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident best dy)");
      check_cuda(
          cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident best score)");
    } catch (...) {
      cudaFree(d_scores);
      cudaFree(d_best_dx);
      cudaFree(d_best_dy);
      cudaFree(d_best_score);
      throw;
    }
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);

    py::dict result;
    result["dx"] = best_dx;
    result["dy"] = best_dy;
    result["score"] = best_score;
    result["search_count"] = shift_count;
    result["sample_stride"] = sample_stride;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_translation_integer_ncc";
    return result;
  }

  py::dict estimate_translation_subpixel_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      float center_dx,
      float center_dy,
      int radius_steps,
      float step,
      int sample_stride) const {
    require_loaded(reference_index, "resident subpixel translation search");
    require_loaded(moving_index, "resident subpixel translation search");
    if (radius_steps < 0) {
      throw std::invalid_argument("radius_steps must be non-negative");
    }
    if (step <= 0.0f) {
      throw std::invalid_argument("step must be positive");
    }
    if (sample_stride <= 0) {
      throw std::invalid_argument("sample_stride must be positive");
    }
    const int candidate_count = (2 * radius_steps + 1) * (2 * radius_steps + 1);
    float* d_scores = nullptr;
    float* d_best_dx = nullptr;
    float* d_best_dy = nullptr;
    float* d_best_score = nullptr;
    float best_dx = 0.0f;
    float best_dy = 0.0f;
    float best_score = 0.0f;
    try {
      check_cuda(cudaMalloc(&d_scores, static_cast<std::size_t>(candidate_count) * sizeof(float)), "cudaMalloc(resident subpixel scores)");
      check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(resident subpixel best dx)");
      check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(resident subpixel best dy)");
      check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(resident subpixel best score)");
      glass_estimate_translation_subpixel_ncc_f32_launch(
          d_stack_ + reference_index * pixels_per_frame_,
          d_stack_ + moving_index * pixels_per_frame_,
          d_scores,
          d_best_dx,
          d_best_dy,
          d_best_score,
          static_cast<int>(width_),
          static_cast<int>(height_),
          center_dx,
          center_dy,
          radius_steps,
          step,
          sample_stride);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.estimate_translation_subpixel_to_reference kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.estimate_translation_subpixel_to_reference synchronize");
      check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident subpixel best dx)");
      check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident subpixel best dy)");
      check_cuda(
          cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident subpixel best score)");
    } catch (...) {
      cudaFree(d_scores);
      cudaFree(d_best_dx);
      cudaFree(d_best_dy);
      cudaFree(d_best_score);
      throw;
    }
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);

    py::dict result;
    result["dx"] = best_dx;
    result["dy"] = best_dy;
    result["score"] = best_score;
    result["candidate_count"] = candidate_count;
    result["center_dx"] = center_dx;
    result["center_dy"] = center_dy;
    result["radius_steps"] = radius_steps;
    result["step"] = step;
    result["sample_stride"] = sample_stride;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_translation_subpixel_ncc";
    return result;
  }

  py::dict frame_global_stats(std::size_t index) const {
    require_loaded(index, "global frame statistics");
    constexpr int threads = 256;
    const int blocks = std::min<int>(
        4096,
        static_cast<int>((pixels_per_frame_ + static_cast<std::size_t>(threads) - 1) / threads));
    double* d_partial_sum = nullptr;
    double* d_partial_sum2 = nullptr;
    unsigned long long* d_partial_count = nullptr;
    std::vector<double> partial_sum(static_cast<std::size_t>(blocks), 0.0);
    std::vector<double> partial_sum2(static_cast<std::size_t>(blocks), 0.0);
    std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);
    try {
      check_cuda(cudaMalloc(&d_partial_sum, partial_sum.size() * sizeof(double)), "cudaMalloc(resident stats sum)");
      check_cuda(cudaMalloc(&d_partial_sum2, partial_sum2.size() * sizeof(double)), "cudaMalloc(resident stats sum2)");
      check_cuda(
          cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
          "cudaMalloc(resident stats count)");
      glass_frame_sum_stats_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_partial_sum,
          d_partial_sum2,
          d_partial_count,
          pixels_per_frame_,
          blocks);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.frame_global_stats kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.frame_global_stats synchronize");
      check_cuda(
          cudaMemcpy(partial_sum.data(), d_partial_sum, partial_sum.size() * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident stats sum)");
      check_cuda(
          cudaMemcpy(partial_sum2.data(), d_partial_sum2, partial_sum2.size() * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident stats sum2)");
      check_cuda(
          cudaMemcpy(
              partial_count.data(),
              d_partial_count,
              partial_count.size() * sizeof(unsigned long long),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident stats count)");
    } catch (...) {
      cudaFree(d_partial_sum);
      cudaFree(d_partial_sum2);
      cudaFree(d_partial_count);
      throw;
    }
    cudaFree(d_partial_sum);
    cudaFree(d_partial_sum2);
    cudaFree(d_partial_count);

    double sum = 0.0;
    double sum2 = 0.0;
    unsigned long long count = 0;
    for (int i = 0; i < blocks; ++i) {
      sum += partial_sum[static_cast<std::size_t>(i)];
      sum2 += partial_sum2[static_cast<std::size_t>(i)];
      count += partial_count[static_cast<std::size_t>(i)];
    }
    const double mean = count > 0 ? sum / static_cast<double>(count) : 0.0;
    double variance = 0.0;
    if (count > 0) {
      variance = sum2 / static_cast<double>(count) - mean * mean;
      if (variance < 0.0) {
        variance = 0.0;
      }
    }
    py::dict result;
    result["mean"] = mean;
    result["std"] = std::sqrt(variance);
    result["valid_pixels"] = count;
    result["total_pixels"] = pixels_per_frame_;
    result["nonfinite_pixels"] = pixels_per_frame_ - static_cast<std::size_t>(count);
    result["model"] = "resident_global_mean_std";
    return result;
  }

  py::dict frame_pair_grid_stats(
      std::size_t reference_index,
      std::size_t source_index,
      int tile_height,
      int tile_width) const {
    require_loaded(reference_index, "grid local normalization reference statistics");
    require_loaded(source_index, "grid local normalization source statistics");
    if (tile_height <= 0 || tile_width <= 0) {
      throw std::invalid_argument("tile dimensions must be positive");
    }
    const int grid_rows =
        (static_cast<int>(height_) + tile_height - 1) / tile_height;
    const int grid_cols =
        (static_cast<int>(width_) + tile_width - 1) / tile_width;
    if (grid_rows <= 0 || grid_cols <= 0) {
      throw std::runtime_error("resident frame shape produced an empty local-normalization grid");
    }
    const std::size_t grid_count =
        static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
    double* d_source_sum = nullptr;
    double* d_source_sum2 = nullptr;
    double* d_reference_sum = nullptr;
    double* d_reference_sum2 = nullptr;
    unsigned long long* d_count = nullptr;
    std::vector<double> source_sum(grid_count, 0.0);
    std::vector<double> source_sum2(grid_count, 0.0);
    std::vector<double> reference_sum(grid_count, 0.0);
    std::vector<double> reference_sum2(grid_count, 0.0);
    std::vector<unsigned long long> count(grid_count, 0);
    try {
      check_cuda(cudaMalloc(&d_source_sum, grid_count * sizeof(double)), "cudaMalloc(resident grid source sum)");
      check_cuda(cudaMalloc(&d_source_sum2, grid_count * sizeof(double)), "cudaMalloc(resident grid source sum2)");
      check_cuda(
          cudaMalloc(&d_reference_sum, grid_count * sizeof(double)),
          "cudaMalloc(resident grid reference sum)");
      check_cuda(
          cudaMalloc(&d_reference_sum2, grid_count * sizeof(double)),
          "cudaMalloc(resident grid reference sum2)");
      check_cuda(
          cudaMalloc(&d_count, grid_count * sizeof(unsigned long long)),
          "cudaMalloc(resident grid valid count)");
      glass_pair_grid_sum_stats_f32_launch(
          d_stack_ + source_index * pixels_per_frame_,
          d_stack_ + reference_index * pixels_per_frame_,
          d_source_sum,
          d_source_sum2,
          d_reference_sum,
          d_reference_sum2,
          d_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          tile_width,
          tile_height,
          grid_cols,
          grid_rows);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.frame_pair_grid_stats kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.frame_pair_grid_stats synchronize");
      check_cuda(
          cudaMemcpy(source_sum.data(), d_source_sum, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid source sum)");
      check_cuda(
          cudaMemcpy(source_sum2.data(), d_source_sum2, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid source sum2)");
      check_cuda(
          cudaMemcpy(reference_sum.data(), d_reference_sum, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid reference sum)");
      check_cuda(
          cudaMemcpy(reference_sum2.data(), d_reference_sum2, grid_count * sizeof(double), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid reference sum2)");
      check_cuda(
          cudaMemcpy(count.data(), d_count, grid_count * sizeof(unsigned long long), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid valid count)");
    } catch (...) {
      cudaFree(d_source_sum);
      cudaFree(d_source_sum2);
      cudaFree(d_reference_sum);
      cudaFree(d_reference_sum2);
      cudaFree(d_count);
      throw;
    }
    cudaFree(d_source_sum);
    cudaFree(d_source_sum2);
    cudaFree(d_reference_sum);
    cudaFree(d_reference_sum2);
    cudaFree(d_count);

    py::array_t<float> source_mean({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<float> source_std({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<float> reference_mean({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<float> reference_std({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    py::array_t<unsigned long long> valid_pixels(
        {static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
    float* source_mean_ptr = static_cast<float*>(source_mean.request().ptr);
    float* source_std_ptr = static_cast<float*>(source_std.request().ptr);
    float* reference_mean_ptr = static_cast<float*>(reference_mean.request().ptr);
    float* reference_std_ptr = static_cast<float*>(reference_std.request().ptr);
    auto* valid_ptr = static_cast<unsigned long long*>(valid_pixels.request().ptr);
    unsigned long long total_count = 0;
    for (std::size_t i = 0; i < grid_count; ++i) {
      const unsigned long long c = count[i];
      total_count += c;
      valid_ptr[i] = c;
      if (c == 0) {
        source_mean_ptr[i] = 0.0f;
        source_std_ptr[i] = 0.0f;
        reference_mean_ptr[i] = 0.0f;
        reference_std_ptr[i] = 0.0f;
        continue;
      }
      const double inv_count = 1.0 / static_cast<double>(c);
      const double s_mean = source_sum[i] * inv_count;
      const double r_mean = reference_sum[i] * inv_count;
      double s_var = source_sum2[i] * inv_count - s_mean * s_mean;
      double r_var = reference_sum2[i] * inv_count - r_mean * r_mean;
      if (s_var < 0.0) {
        s_var = 0.0;
      }
      if (r_var < 0.0) {
        r_var = 0.0;
      }
      source_mean_ptr[i] = static_cast<float>(s_mean);
      source_std_ptr[i] = static_cast<float>(std::sqrt(s_var));
      reference_mean_ptr[i] = static_cast<float>(r_mean);
      reference_std_ptr[i] = static_cast<float>(std::sqrt(r_var));
    }

    py::dict result;
    result["source_mean"] = source_mean;
    result["source_std"] = source_std;
    result["reference_mean"] = reference_mean;
    result["reference_std"] = reference_std;
    result["valid_pixels"] = valid_pixels;
    result["grid_rows"] = grid_rows;
    result["grid_cols"] = grid_cols;
    result["tile_height"] = tile_height;
    result["tile_width"] = tile_width;
    result["valid_pixel_total"] = total_count;
    result["model"] = "resident_grid_pair_mean_std";
    return result;
  }

  py::dict frame_pair_grid_stats_batch(
      std::size_t reference_index,
      py::array_t<int, py::array::c_style | py::array::forcecast> source_indices,
      int tile_height,
      int tile_width) const {
    require_loaded(reference_index, "batched grid local normalization reference statistics");
    const py::buffer_info source_info = source_indices.request();
    if (source_info.ndim != 1) {
      throw std::invalid_argument("source_indices must be a one-dimensional array");
    }
    const int source_count = static_cast<int>(source_info.shape[0]);
    if (tile_height <= 0 || tile_width <= 0) {
      throw std::invalid_argument("tile dimensions must be positive");
    }
    const int grid_rows =
        (static_cast<int>(height_) + tile_height - 1) / tile_height;
    const int grid_cols =
        (static_cast<int>(width_) + tile_width - 1) / tile_width;
    if (grid_rows <= 0 || grid_cols <= 0) {
      throw std::runtime_error("resident frame shape produced an empty local-normalization grid");
    }
    const std::size_t grid_count =
        static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
    const auto* source_ptr = static_cast<const int*>(source_info.ptr);
    std::vector<int> host_source_indices(static_cast<std::size_t>(source_count), 0);
    for (int i = 0; i < source_count; ++i) {
      const int source_index = source_ptr[i];
      if (source_index < 0 || static_cast<std::size_t>(source_index) >= frame_count_) {
        throw std::out_of_range("source index is out of resident stack range");
      }
      require_loaded(static_cast<std::size_t>(source_index), "batched grid local normalization source statistics");
      host_source_indices[static_cast<std::size_t>(i)] = source_index;
    }

    const std::size_t total_grid_count = grid_count * static_cast<std::size_t>(source_count);
    std::vector<double> source_sum(total_grid_count, 0.0);
    std::vector<double> source_sum2(total_grid_count, 0.0);
    std::vector<double> reference_sum(total_grid_count, 0.0);
    std::vector<double> reference_sum2(total_grid_count, 0.0);
    std::vector<unsigned long long> count(total_grid_count, 0);
    int* d_source_indices = nullptr;
    double* d_source_sum = nullptr;
    double* d_source_sum2 = nullptr;
    double* d_reference_sum = nullptr;
    double* d_reference_sum2 = nullptr;
    unsigned long long* d_count = nullptr;
    double index_upload_s = 0.0;
    double allocation_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    const auto total_start = Clock::now();
    try {
      if (source_count > 0) {
        const auto alloc_start = Clock::now();
        check_cuda(
            cudaMalloc(&d_source_indices, host_source_indices.size() * sizeof(int)),
            "cudaMalloc(resident batch grid source indices)");
        check_cuda(
            cudaMalloc(&d_source_sum, total_grid_count * sizeof(double)),
            "cudaMalloc(resident batch grid source sum)");
        check_cuda(
            cudaMalloc(&d_source_sum2, total_grid_count * sizeof(double)),
            "cudaMalloc(resident batch grid source sum2)");
        check_cuda(
            cudaMalloc(&d_reference_sum, total_grid_count * sizeof(double)),
            "cudaMalloc(resident batch grid reference sum)");
        check_cuda(
            cudaMalloc(&d_reference_sum2, total_grid_count * sizeof(double)),
            "cudaMalloc(resident batch grid reference sum2)");
        check_cuda(
            cudaMalloc(&d_count, total_grid_count * sizeof(unsigned long long)),
            "cudaMalloc(resident batch grid valid count)");
        allocation_s = seconds_since(alloc_start);

        const auto upload_start = Clock::now();
        check_cuda(
            cudaMemcpy(
                d_source_indices,
                host_source_indices.data(),
                host_source_indices.size() * sizeof(int),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident batch grid source indices)");
        index_upload_s = seconds_since(upload_start);

        const auto kernel_start = Clock::now();
        glass_pair_grid_sum_stats_batch_f32_launch(
            d_stack_,
            d_source_indices,
            source_count,
            static_cast<int>(reference_index),
            d_source_sum,
            d_source_sum2,
            d_reference_sum,
            d_reference_sum2,
            d_count,
            pixels_per_frame_,
            static_cast<int>(width_),
            static_cast<int>(height_),
            tile_width,
            tile_height,
            grid_cols,
            grid_rows);
        kernel_enqueue_s = seconds_since(kernel_start);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.frame_pair_grid_stats_batch kernel launch");
        const auto sync_start = Clock::now();
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.frame_pair_grid_stats_batch synchronize");
        sync_s = seconds_since(sync_start);

        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(source_sum.data(), d_source_sum, total_grid_count * sizeof(double), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid source sum)");
        check_cuda(
            cudaMemcpy(source_sum2.data(), d_source_sum2, total_grid_count * sizeof(double), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid source sum2)");
        check_cuda(
            cudaMemcpy(
                reference_sum.data(),
                d_reference_sum,
                total_grid_count * sizeof(double),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid reference sum)");
        check_cuda(
            cudaMemcpy(
                reference_sum2.data(),
                d_reference_sum2,
                total_grid_count * sizeof(double),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid reference sum2)");
        check_cuda(
            cudaMemcpy(count.data(), d_count, total_grid_count * sizeof(unsigned long long), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid valid count)");
        download_s = seconds_since(download_start);
      }
    } catch (...) {
      cudaFree(d_source_indices);
      cudaFree(d_source_sum);
      cudaFree(d_source_sum2);
      cudaFree(d_reference_sum);
      cudaFree(d_reference_sum2);
      cudaFree(d_count);
      throw;
    }
    cudaFree(d_source_indices);
    cudaFree(d_source_sum);
    cudaFree(d_source_sum2);
    cudaFree(d_reference_sum);
    cudaFree(d_reference_sum2);
    cudaFree(d_count);

    py::list frames;
    for (int source_position = 0; source_position < source_count; ++source_position) {
      py::array_t<float> source_mean({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
      py::array_t<float> source_std({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
      py::array_t<float> reference_mean({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
      py::array_t<float> reference_std({static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
      py::array_t<unsigned long long> valid_pixels(
          {static_cast<py::ssize_t>(grid_rows), static_cast<py::ssize_t>(grid_cols)});
      float* source_mean_ptr = static_cast<float*>(source_mean.request().ptr);
      float* source_std_ptr = static_cast<float*>(source_std.request().ptr);
      float* reference_mean_ptr = static_cast<float*>(reference_mean.request().ptr);
      float* reference_std_ptr = static_cast<float*>(reference_std.request().ptr);
      auto* valid_ptr = static_cast<unsigned long long*>(valid_pixels.request().ptr);
      unsigned long long total_count = 0;
      const std::size_t source_offset = static_cast<std::size_t>(source_position) * grid_count;
      for (std::size_t tile_index = 0; tile_index < grid_count; ++tile_index) {
        const std::size_t i = source_offset + tile_index;
        const unsigned long long c = count[i];
        total_count += c;
        valid_ptr[tile_index] = c;
        if (c == 0) {
          source_mean_ptr[tile_index] = 0.0f;
          source_std_ptr[tile_index] = 0.0f;
          reference_mean_ptr[tile_index] = 0.0f;
          reference_std_ptr[tile_index] = 0.0f;
          continue;
        }
        const double inv_count = 1.0 / static_cast<double>(c);
        const double s_mean = source_sum[i] * inv_count;
        const double r_mean = reference_sum[i] * inv_count;
        double s_var = source_sum2[i] * inv_count - s_mean * s_mean;
        double r_var = reference_sum2[i] * inv_count - r_mean * r_mean;
        if (s_var < 0.0) {
          s_var = 0.0;
        }
        if (r_var < 0.0) {
          r_var = 0.0;
        }
        source_mean_ptr[tile_index] = static_cast<float>(s_mean);
        source_std_ptr[tile_index] = static_cast<float>(std::sqrt(s_var));
        reference_mean_ptr[tile_index] = static_cast<float>(r_mean);
        reference_std_ptr[tile_index] = static_cast<float>(std::sqrt(r_var));
      }
      py::dict frame;
      frame["source_mean"] = source_mean;
      frame["source_std"] = source_std;
      frame["reference_mean"] = reference_mean;
      frame["reference_std"] = reference_std;
      frame["valid_pixels"] = valid_pixels;
      frame["grid_rows"] = grid_rows;
      frame["grid_cols"] = grid_cols;
      frame["tile_height"] = tile_height;
      frame["tile_width"] = tile_width;
      frame["valid_pixel_total"] = total_count;
      frame["model"] = "resident_grid_pair_mean_std";
      frame["source_index"] = host_source_indices[static_cast<std::size_t>(source_position)];
      frame["reference_index"] = static_cast<unsigned long long>(reference_index);
      frame["batch_position"] = source_position;
      frames.append(frame);
    }

    py::dict result;
    result["schema_version"] = 1;
    result["model"] = "resident_grid_pair_mean_std_batch";
    result["batch_model"] = "single_kernel_source_frame_tile_grid";
    result["reference_index"] = static_cast<unsigned long long>(reference_index);
    result["source_count"] = source_count;
    result["grid_rows"] = grid_rows;
    result["grid_cols"] = grid_cols;
    result["grid_count"] = static_cast<unsigned long long>(grid_count);
    result["tile_height"] = tile_height;
    result["tile_width"] = tile_width;
    result["source_indices"] = source_indices;
    result["allocation_s"] = allocation_s;
    result["index_upload_s"] = index_upload_s;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["sync_s"] = sync_s;
    result["download_s"] = download_s;
    result["total_s"] = seconds_since(total_start);
    result["download_bytes"] = static_cast<unsigned long long>(
        total_grid_count * (4 * sizeof(double) + sizeof(unsigned long long)));
    result["index_bytes"] = static_cast<unsigned long long>(host_source_indices.size() * sizeof(int));
    result["frames"] = frames;
    return result;
  }

  py::dict apply_global_normalization_frame(std::size_t index, float scale, float offset) {
    require_loaded(index, "global local normalization");
    const auto total_start = Clock::now();
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    try {
      float* frame = d_stack_ + index * pixels_per_frame_;
      const auto kernel_start = Clock::now();
      glass_local_norm_apply_f32_launch(frame, frame, pixels_per_frame_, scale, offset);
      kernel_enqueue_s = seconds_since(kernel_start);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_global_normalization_frame kernel launch");
      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_global_normalization_frame synchronize");
      sync_s = seconds_since(sync_start);
    } catch (...) {
      throw;
    }
    py::dict result;
    result["schema_version"] = 1;
    result["mode"] = "in_place_device_update";
    result["model"] = "resident_global_mean_std";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["frame_bytes"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float));
    result["temporary_output_bytes"] = static_cast<unsigned long long>(0);
    result["device_to_device_copy_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_grid_normalization_frame(
      std::size_t index,
      py::array_t<float, py::array::c_style | py::array::forcecast> scales,
      py::array_t<float, py::array::c_style | py::array::forcecast> offsets,
      int tile_height,
      int tile_width) {
    require_loaded(index, "grid local normalization");
    const py::buffer_info scales_info = scales.request();
    const py::buffer_info offsets_info = offsets.request();
    if (scales_info.ndim != 2 || offsets_info.ndim != 2) {
      throw std::invalid_argument("scales and offsets must have shape (grid_rows, grid_cols)");
    }
    if (scales_info.shape[0] != offsets_info.shape[0] || scales_info.shape[1] != offsets_info.shape[1]) {
      throw std::invalid_argument("scales and offsets shapes must match");
    }
    if (tile_height <= 0 || tile_width <= 0) {
      throw std::invalid_argument("tile dimensions must be positive");
    }
    const int grid_rows = static_cast<int>(scales_info.shape[0]);
    const int grid_cols = static_cast<int>(scales_info.shape[1]);
    if (grid_rows <= 0 || grid_cols <= 0) {
      throw std::invalid_argument("coefficient grid must not be empty");
    }
    const int expected_rows =
        (static_cast<int>(height_) + tile_height - 1) / tile_height;
    const int expected_cols =
        (static_cast<int>(width_) + tile_width - 1) / tile_width;
    if (grid_rows != expected_rows || grid_cols != expected_cols) {
      throw std::invalid_argument("coefficient grid shape does not match resident frame shape and tile dimensions");
    }
    const std::size_t coefficient_count =
        static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
    const auto total_start = Clock::now();
    double coefficient_alloc_s = 0.0;
    double coefficient_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    float* d_scales = nullptr;
    float* d_offsets = nullptr;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(
          cudaMalloc(&d_scales, coefficient_count * sizeof(float)),
          "cudaMalloc(resident grid normalization scales)");
      check_cuda(
          cudaMalloc(&d_offsets, coefficient_count * sizeof(float)),
          "cudaMalloc(resident grid normalization offsets)");
      coefficient_alloc_s = seconds_since(alloc_start);
      const auto upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_scales, scales_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident grid normalization scales)");
      check_cuda(
          cudaMemcpy(d_offsets, offsets_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident grid normalization offsets)");
      coefficient_upload_s = seconds_since(upload_start);
      float* frame = d_stack_ + index * pixels_per_frame_;
      const auto kernel_start = Clock::now();
      glass_local_norm_apply_grid_f32_launch(
          frame,
          frame,
          d_scales,
          d_offsets,
          static_cast<int>(width_),
          static_cast<int>(height_),
          tile_width,
          tile_height,
          grid_cols,
          grid_rows);
      kernel_enqueue_s = seconds_since(kernel_start);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_grid_normalization_frame kernel launch");
      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_grid_normalization_frame synchronize");
      sync_s = seconds_since(sync_start);
    } catch (...) {
      cudaFree(d_scales);
      cudaFree(d_offsets);
      throw;
    }
    cudaFree(d_scales);
    cudaFree(d_offsets);
    py::dict result;
    result["schema_version"] = 1;
    result["mode"] = "in_place_device_update";
    result["model"] = "resident_grid_mean_std";
    result["frame_index"] = static_cast<unsigned long long>(index);
    result["frame_bytes"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float));
    result["temporary_output_bytes"] = static_cast<unsigned long long>(0);
    result["coefficient_count"] = static_cast<unsigned long long>(coefficient_count);
    result["coefficient_bytes"] = static_cast<unsigned long long>(coefficient_count * sizeof(float) * 2);
    result["coefficient_alloc_s"] = coefficient_alloc_s;
    result["coefficient_upload_s"] = coefficient_upload_s;
    result["device_to_device_copy_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    return result;
  }

  py::dict apply_grid_normalization_frames(
      py::array_t<int, py::array::c_style | py::array::forcecast> frame_indices,
      py::array_t<float, py::array::c_style | py::array::forcecast> scales,
      py::array_t<float, py::array::c_style | py::array::forcecast> offsets,
      int tile_height,
      int tile_width) {
    const py::buffer_info indices_info = frame_indices.request();
    const py::buffer_info scales_info = scales.request();
    const py::buffer_info offsets_info = offsets.request();
    if (indices_info.ndim != 1) {
      throw std::invalid_argument("frame_indices must be a one-dimensional array");
    }
    if (scales_info.ndim != 3 || offsets_info.ndim != 3) {
      throw std::invalid_argument("scales and offsets must have shape (frame_count, grid_rows, grid_cols)");
    }
    if (scales_info.shape[0] != indices_info.shape[0] || offsets_info.shape[0] != indices_info.shape[0]) {
      throw std::invalid_argument("coefficient frame count must match frame_indices length");
    }
    if (
        scales_info.shape[1] != offsets_info.shape[1] ||
        scales_info.shape[2] != offsets_info.shape[2]) {
      throw std::invalid_argument("scales and offsets grid shapes must match");
    }
    if (tile_height <= 0 || tile_width <= 0) {
      throw std::invalid_argument("tile dimensions must be positive");
    }
    const int frame_count = static_cast<int>(indices_info.shape[0]);
    const int grid_rows = static_cast<int>(scales_info.shape[1]);
    const int grid_cols = static_cast<int>(scales_info.shape[2]);
    if (frame_count <= 0) {
      py::dict result;
      result["schema_version"] = 1;
      result["mode"] = "in_place_device_update_batch";
      result["model"] = "resident_grid_mean_std_batch_apply";
      result["frame_count"] = 0;
      result["grid_rows"] = grid_rows;
      result["grid_cols"] = grid_cols;
      result["grid_count"] = 0;
      result["coefficient_count"] = 0;
      result["coefficient_bytes"] = static_cast<unsigned long long>(0);
      result["coefficient_alloc_s"] = 0.0;
      result["coefficient_upload_s"] = 0.0;
      result["kernel_enqueue_s"] = 0.0;
      result["sync_s"] = 0.0;
      result["total_s"] = 0.0;
      result["frames"] = py::list();
      return result;
    }
    if (grid_rows <= 0 || grid_cols <= 0) {
      throw std::invalid_argument("coefficient grid must not be empty");
    }
    const int expected_rows =
        (static_cast<int>(height_) + tile_height - 1) / tile_height;
    const int expected_cols =
        (static_cast<int>(width_) + tile_width - 1) / tile_width;
    if (grid_rows != expected_rows || grid_cols != expected_cols) {
      throw std::invalid_argument("coefficient grid shape does not match resident frame shape and tile dimensions");
    }
    const int* index_ptr = static_cast<const int*>(indices_info.ptr);
    std::vector<int> host_indices(static_cast<std::size_t>(frame_count), 0);
    for (int i = 0; i < frame_count; ++i) {
      const int frame_index = index_ptr[i];
      if (frame_index < 0 || static_cast<std::size_t>(frame_index) >= frame_count_) {
        throw std::out_of_range("frame index is out of resident stack range");
      }
      require_loaded(static_cast<std::size_t>(frame_index), "batched grid local normalization");
      host_indices[static_cast<std::size_t>(i)] = frame_index;
    }
    const std::size_t grid_count =
        static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
    const std::size_t coefficient_count =
        static_cast<std::size_t>(frame_count) * grid_count;
    const auto total_start = Clock::now();
    double coefficient_alloc_s = 0.0;
    double coefficient_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    float* d_scales = nullptr;
    float* d_offsets = nullptr;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(
          cudaMalloc(&d_scales, coefficient_count * sizeof(float)),
          "cudaMalloc(resident batch grid normalization scales)");
      check_cuda(
          cudaMalloc(&d_offsets, coefficient_count * sizeof(float)),
          "cudaMalloc(resident batch grid normalization offsets)");
      coefficient_alloc_s = seconds_since(alloc_start);
      const auto upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_scales, scales_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident batch grid normalization scales)");
      check_cuda(
          cudaMemcpy(d_offsets, offsets_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident batch grid normalization offsets)");
      coefficient_upload_s = seconds_since(upload_start);
      const auto kernel_start = Clock::now();
      for (int batch_position = 0; batch_position < frame_count; ++batch_position) {
        const std::size_t coefficient_offset =
            static_cast<std::size_t>(batch_position) * grid_count;
        float* frame = d_stack_ + static_cast<std::size_t>(host_indices[static_cast<std::size_t>(batch_position)]) * pixels_per_frame_;
        glass_local_norm_apply_grid_f32_launch(
            frame,
            frame,
            d_scales + coefficient_offset,
            d_offsets + coefficient_offset,
            static_cast<int>(width_),
            static_cast<int>(height_),
            tile_width,
            tile_height,
            grid_cols,
            grid_rows);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.apply_grid_normalization_frames kernel launch");
      }
      kernel_enqueue_s = seconds_since(kernel_start);
      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.apply_grid_normalization_frames synchronize");
      sync_s = seconds_since(sync_start);
    } catch (...) {
      cudaFree(d_scales);
      cudaFree(d_offsets);
      throw;
    }
    cudaFree(d_scales);
    cudaFree(d_offsets);

    py::list frame_profiles;
    const double inv_frame_count = 1.0 / static_cast<double>(frame_count);
    for (int batch_position = 0; batch_position < frame_count; ++batch_position) {
      py::dict frame_profile;
      frame_profile["schema_version"] = 1;
      frame_profile["mode"] = "in_place_device_update_batch";
      frame_profile["model"] = "resident_grid_mean_std";
      frame_profile["frame_index"] = static_cast<unsigned long long>(
          host_indices[static_cast<std::size_t>(batch_position)]);
      frame_profile["batch_position"] = batch_position;
      frame_profile["frame_bytes"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float));
      frame_profile["temporary_output_bytes"] = static_cast<unsigned long long>(0);
      frame_profile["coefficient_count"] = static_cast<unsigned long long>(grid_count);
      frame_profile["coefficient_bytes"] = static_cast<unsigned long long>(grid_count * sizeof(float) * 2);
      frame_profile["coefficient_alloc_s"] = coefficient_alloc_s * inv_frame_count;
      frame_profile["coefficient_upload_s"] = coefficient_upload_s * inv_frame_count;
      frame_profile["device_to_device_copy_s"] = 0.0;
      frame_profile["kernel_enqueue_s"] = kernel_enqueue_s * inv_frame_count;
      frame_profile["sync_s"] = sync_s * inv_frame_count;
      frame_profile["total_s"] = seconds_since(total_start) * inv_frame_count;
      frame_profiles.append(frame_profile);
    }
    py::dict result;
    result["schema_version"] = 1;
    result["mode"] = "in_place_device_update_batch";
    result["model"] = "resident_grid_mean_std_batch_apply";
    result["frame_count"] = frame_count;
    result["grid_rows"] = grid_rows;
    result["grid_cols"] = grid_cols;
    result["grid_count"] = static_cast<unsigned long long>(grid_count);
    result["tile_height"] = tile_height;
    result["tile_width"] = tile_width;
    result["frame_indices"] = frame_indices;
    result["frame_bytes"] = static_cast<unsigned long long>(
        static_cast<std::size_t>(frame_count) * pixels_per_frame_ * sizeof(float));
    result["temporary_output_bytes"] = static_cast<unsigned long long>(0);
    result["coefficient_count"] = static_cast<unsigned long long>(coefficient_count);
    result["coefficient_bytes"] = static_cast<unsigned long long>(coefficient_count * sizeof(float) * 2);
    result["coefficient_alloc_s"] = coefficient_alloc_s;
    result["coefficient_upload_s"] = coefficient_upload_s;
    result["device_to_device_copy_s"] = 0.0;
    result["kernel_enqueue_s"] = kernel_enqueue_s;
    result["sync_s"] = sync_s;
    result["total_s"] = seconds_since(total_start);
    result["frames"] = frame_profiles;
    return result;
  }

  py::array_t<unsigned char> star_local_max_mask(std::size_t index, float threshold) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    py::array_t<unsigned char> mask({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info mask_info = mask.request();
    unsigned char* d_mask = nullptr;
    try {
      check_cuda(cudaMalloc(&d_mask, pixels_per_frame_ * sizeof(unsigned char)), "cudaMalloc(resident star mask)");
      glass_star_local_max_mask_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_mask,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_local_max_mask kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_local_max_mask synchronize");
      check_cuda(
          cudaMemcpy(mask_info.ptr, d_mask, pixels_per_frame_ * sizeof(unsigned char), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident star mask)");
    } catch (...) {
      cudaFree(d_mask);
      throw;
    }
    cudaFree(d_mask);
    return mask;
  }

  py::dict star_candidates(std::size_t index, float threshold, int max_candidates) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (max_candidates <= 0) {
      throw std::invalid_argument("max_candidates must be positive");
    }
    py::array_t<float> xs({max_candidates});
    py::array_t<float> ys({max_candidates});
    py::array_t<float> fluxes({max_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int total_count = 0;
    try {
      check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star xs)");
      check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
          "cudaMalloc(star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(star count)");
      glass_star_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          max_candidates);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_candidates synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(star count)");
      const int stored_count = total_count < max_candidates ? total_count : max_candidates;
      check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star xs)");
      check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star ys)");
      check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      return result;
    } catch (...) {
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      throw;
    }
  }

  py::dict star_top_candidates(std::size_t index, float threshold, int max_candidates) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (max_candidates <= 0) {
      throw std::invalid_argument("max_candidates must be positive");
    }
    py::array_t<float> xs({max_candidates});
    py::array_t<float> ys({max_candidates});
    py::array_t<float> fluxes({max_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_lock = nullptr;
    int total_count = 0;
    try {
      check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star xs)");
      check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
          "cudaMalloc(top star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(top star count)");
      check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(top star lock)");
      glass_star_top_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          d_lock,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          max_candidates);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_top_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_top_candidates synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(top star count)");
      const int stored_count = total_count < max_candidates ? total_count : max_candidates;
      check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star xs)");
      check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star ys)");
      check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      return result;
    } catch (...) {
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      throw;
    }
  }

  py::dict star_top_nms_candidates(
      std::size_t index,
      float threshold,
      int scan_candidates,
      int max_output_candidates,
      float min_separation_px) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (scan_candidates <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("candidate counts must be positive");
    }
    if (scan_candidates < max_output_candidates) {
      throw std::invalid_argument("scan_candidates must be greater than or equal to max_output_candidates");
    }
    if (min_separation_px < 0.0f) {
      throw std::invalid_argument("min_separation_px must be non-negative");
    }
    py::array_t<float> xs({max_output_candidates});
    py::array_t<float> ys({max_output_candidates});
    py::array_t<float> fluxes({max_output_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_scan_xs = nullptr;
    float* d_scan_ys = nullptr;
    float* d_scan_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_lock = nullptr;
    int* d_stored_count = nullptr;
    int total_count = 0;
    int stored_count = 0;
    try {
      check_cuda(
          cudaMalloc(&d_scan_xs, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan xs)");
      check_cuda(
          cudaMalloc(&d_scan_ys, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan ys)");
      check_cuda(
          cudaMalloc(&d_scan_fluxes, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan fluxes)");
      check_cuda(
          cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star xs)");
      check_cuda(
          cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(resident top nms star count)");
      check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(resident top nms star lock)");
      check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(resident top nms stored count)");
      glass_star_top_nms_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_scan_xs,
          d_scan_ys,
          d_scan_fluxes,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          d_lock,
          d_stored_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          scan_candidates,
          max_output_candidates,
          min_separation_px);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_top_nms_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_top_nms_candidates synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident top nms count)");
      check_cuda(
          cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms stored count)");
      check_cuda(
          cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms star xs)");
      check_cuda(
          cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms star ys)");
      check_cuda(
          cudaMemcpy(
              flux_info.ptr,
              d_fluxes,
              static_cast<std::size_t>(stored_count) * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["scan_candidates"] = scan_candidates;
      result["max_output_candidates"] = max_output_candidates;
      result["min_separation_px"] = min_separation_px;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_scan_xs);
      cudaFree(d_scan_ys);
      cudaFree(d_scan_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      cudaFree(d_stored_count);
      return result;
    } catch (...) {
      cudaFree(d_scan_xs);
      cudaFree(d_scan_ys);
      cudaFree(d_scan_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      cudaFree(d_stored_count);
      throw;
    }
  }

  py::dict star_top_nms_candidates_centroid(
      std::size_t index,
      float threshold,
      int scan_candidates,
      int max_output_candidates,
      float min_separation_px,
      int centroid_radius,
      bool centroid_global_mean_background = false) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (scan_candidates <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("candidate counts must be positive");
    }
    if (scan_candidates < max_output_candidates) {
      throw std::invalid_argument("scan_candidates must be greater than or equal to max_output_candidates");
    }
    py::array_t<float> xs({max_output_candidates});
    py::array_t<float> ys({max_output_candidates});
    py::array_t<float> fluxes({max_output_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_scan_xs = nullptr;
    float* d_scan_ys = nullptr;
    float* d_scan_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_lock = nullptr;
    int* d_stored_count = nullptr;
    unsigned char* d_refine_status = nullptr;
    int total_count = 0;
    int stored_count = 0;
    try {
      check_cuda(
          cudaMalloc(&d_scan_xs, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan xs centroid)");
      check_cuda(
          cudaMalloc(&d_scan_ys, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan ys centroid)");
      check_cuda(
          cudaMalloc(&d_scan_fluxes, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms scan fluxes centroid)");
      check_cuda(
          cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star xs centroid)");
      check_cuda(
          cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star ys centroid)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident top nms star fluxes centroid)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(resident top nms count centroid)");
      check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(resident top nms lock centroid)");
      check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(resident top nms stored count centroid)");
      glass_star_top_nms_candidates_f32_launch(
          d_stack_ + index * pixels_per_frame_,
          d_scan_xs,
          d_scan_ys,
          d_scan_fluxes,
          d_xs,
          d_ys,
          d_fluxes,
          d_count,
          d_lock,
          d_stored_count,
          static_cast<int>(width_),
          static_cast<int>(height_),
          threshold,
          scan_candidates,
          max_output_candidates,
          min_separation_px);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_top_nms_candidates_centroid kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_top_nms_candidates_centroid synchronize");
      check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(resident top nms count centroid)");
      check_cuda(
          cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident top nms stored count centroid)");
      std::vector<float> centroid_before_xs;
      std::vector<float> centroid_before_ys;
      std::vector<unsigned char> centroid_statuses;
      float centroid_background = std::numeric_limits<float>::quiet_NaN();
      const char* centroid_background_mode = "local_median";
      if (centroid_radius > 0 && stored_count > 0) {
        if (centroid_global_mean_background) {
          centroid_background = device_frame_mean_f32(
              d_stack_ + index * pixels_per_frame_,
              pixels_per_frame_,
              "cudaMalloc(resident top nms centroid background)");
          centroid_background_mode = "global_mean";
        }
        centroid_before_xs.resize(static_cast<std::size_t>(stored_count));
        centroid_before_ys.resize(static_cast<std::size_t>(stored_count));
        centroid_statuses.resize(static_cast<std::size_t>(stored_count));
        check_cuda(
            cudaMemcpy(
                centroid_before_xs.data(),
                d_xs,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident top nms centroid original xs)");
        check_cuda(
            cudaMemcpy(
                centroid_before_ys.data(),
                d_ys,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident top nms centroid original ys)");
        check_cuda(
            cudaMalloc(&d_refine_status, static_cast<std::size_t>(stored_count) * sizeof(unsigned char)),
            "cudaMalloc(resident top nms centroid status)");
        glass_star_refine_centroids_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_xs,
            d_ys,
            d_fluxes,
            d_refine_status,
            stored_count,
            static_cast<int>(width_),
            static_cast<int>(height_),
            centroid_radius,
            centroid_background);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_top_nms_candidates_centroid refine kernel launch");
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_top_nms_candidates_centroid refine synchronize");
        check_cuda(
            cudaMemcpy(
                centroid_statuses.data(),
                d_refine_status,
                static_cast<std::size_t>(stored_count) * sizeof(unsigned char),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident top nms centroid status)");
      }
      check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident top nms star xs centroid)");
      check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident top nms star ys centroid)");
      check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident top nms star fluxes centroid)");
      py::dict centroid_refine = centroid_refine_summary(
          centroid_radius,
          stored_count,
          centroid_before_xs,
          centroid_before_ys,
          static_cast<const float*>(xs_info.ptr),
          static_cast<const float*>(ys_info.ptr),
          centroid_statuses);
      centroid_refine["background_mode"] = centroid_radius > 0 ? centroid_background_mode : "off";
      centroid_refine["mode"] = centroid_radius > 0
          ? (centroid_global_mean_background ? "resident_gpu_global_mean_centroid" : "resident_gpu_window_centroid")
          : "off";
      if (std::isfinite(centroid_background)) {
        centroid_refine["background"] = centroid_background;
      } else {
        centroid_refine["background"] = py::none();
      }
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["scan_candidates"] = scan_candidates;
      result["max_output_candidates"] = max_output_candidates;
      result["min_separation_px"] = min_separation_px;
      result["centroid_refine"] = centroid_refine;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_scan_xs);
      cudaFree(d_scan_ys);
      cudaFree(d_scan_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      cudaFree(d_stored_count);
      cudaFree(d_refine_status);
      return result;
    } catch (...) {
      cudaFree(d_scan_xs);
      cudaFree(d_scan_ys);
      cudaFree(d_scan_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_lock);
      cudaFree(d_stored_count);
      throw;
    }
  }

  py::dict star_grid_top_nms_candidates_impl(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      bool deterministic,
      int centroid_radius = 0,
      bool centroid_global_mean_background = false) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error("resident frame must be loaded before star detection");
    }
    if (grid_cols <= 0 || grid_rows <= 0 || candidates_per_cell <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("grid dimensions and candidate counts must be positive");
    }
    if (min_separation_px < 0.0f) {
      throw std::invalid_argument("min_separation_px must be non-negative");
    }
    const int cell_count = grid_cols * grid_rows;
    const int grid_capacity = cell_count * candidates_per_cell;
    py::array_t<float> xs({max_output_candidates});
    py::array_t<float> ys({max_output_candidates});
    py::array_t<float> fluxes({max_output_candidates});
    const py::buffer_info xs_info = xs.request();
    const py::buffer_info ys_info = ys.request();
    const py::buffer_info flux_info = fluxes.request();

    float* d_grid_xs = nullptr;
    float* d_grid_ys = nullptr;
    float* d_grid_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_locks = nullptr;
    int* d_cell_counts = nullptr;
    int* d_stored_count = nullptr;
    unsigned char* d_refine_status = nullptr;
    int total_count = 0;
    int stored_count = 0;
    try {
      check_cuda(
          cudaMalloc(&d_grid_xs, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident grid top nms grid xs)");
      check_cuda(
          cudaMalloc(&d_grid_ys, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident grid top nms grid ys)");
      check_cuda(
          cudaMalloc(&d_grid_fluxes, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
          "cudaMalloc(resident grid top nms grid fluxes)");
      check_cuda(
          cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident grid top nms star xs)");
      check_cuda(
          cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident grid top nms star ys)");
      check_cuda(
          cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
          "cudaMalloc(resident grid top nms star fluxes)");
      check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(resident grid top nms star count)");
      check_cuda(
          cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident grid top nms locks)");
      check_cuda(
          cudaMalloc(&d_cell_counts, static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident grid top nms cell counts)");
      check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(resident grid top nms stored count)");
      if (deterministic) {
        glass_star_grid_top_nms_candidates_deterministic_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_grid_xs,
            d_grid_ys,
            d_grid_fluxes,
            d_xs,
            d_ys,
            d_fluxes,
            d_count,
            d_stored_count,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows,
            candidates_per_cell,
            max_output_candidates,
            min_separation_px);
      } else {
        glass_star_grid_top_nms_candidates_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_grid_xs,
            d_grid_ys,
            d_grid_fluxes,
            d_xs,
            d_ys,
            d_fluxes,
            d_count,
            d_locks,
            d_cell_counts,
            d_stored_count,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows,
            candidates_per_cell,
            max_output_candidates,
            min_separation_px);
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_grid_top_nms_candidates kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_grid_top_nms_candidates synchronize");
      check_cuda(
          cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms count)");
      check_cuda(
          cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms stored count)");
      std::vector<float> centroid_before_xs;
      std::vector<float> centroid_before_ys;
      std::vector<unsigned char> centroid_statuses;
      float centroid_background = std::numeric_limits<float>::quiet_NaN();
      const char* centroid_background_mode = "local_median";
      if (centroid_radius > 0 && stored_count > 0) {
        if (centroid_global_mean_background) {
          centroid_background = device_frame_mean_f32(
              d_stack_ + index * pixels_per_frame_,
              pixels_per_frame_,
              "cudaMalloc(resident grid top nms centroid background)");
          centroid_background_mode = "global_mean";
        }
        centroid_before_xs.resize(static_cast<std::size_t>(stored_count));
        centroid_before_ys.resize(static_cast<std::size_t>(stored_count));
        centroid_statuses.resize(static_cast<std::size_t>(stored_count));
        check_cuda(
            cudaMemcpy(
                centroid_before_xs.data(),
                d_xs,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident grid top nms centroid original xs)");
        check_cuda(
            cudaMemcpy(
                centroid_before_ys.data(),
                d_ys,
                static_cast<std::size_t>(stored_count) * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident grid top nms centroid original ys)");
        check_cuda(
            cudaMalloc(&d_refine_status, static_cast<std::size_t>(stored_count) * sizeof(unsigned char)),
            "cudaMalloc(resident grid top nms centroid status)");
        glass_star_refine_centroids_f32_launch(
            d_stack_ + index * pixels_per_frame_,
            d_xs,
            d_ys,
            d_fluxes,
            d_refine_status,
            stored_count,
            static_cast<int>(width_),
            static_cast<int>(height_),
            centroid_radius,
            centroid_background);
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_grid_top_nms_candidates centroid refine kernel launch");
        check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star_grid_top_nms_candidates centroid refine synchronize");
        check_cuda(
            cudaMemcpy(
                centroid_statuses.data(),
                d_refine_status,
                static_cast<std::size_t>(stored_count) * sizeof(unsigned char),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident grid top nms centroid status)");
      }
      check_cuda(
          cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms star xs)");
      check_cuda(
          cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms star ys)");
      check_cuda(
          cudaMemcpy(
              flux_info.ptr,
              d_fluxes,
              static_cast<std::size_t>(stored_count) * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident grid top nms star fluxes)");
      py::dict result;
      result["count"] = total_count;
      result["stored_count"] = stored_count;
      result["grid_cols"] = grid_cols;
      result["grid_rows"] = grid_rows;
      result["candidates_per_cell"] = candidates_per_cell;
      result["max_output_candidates"] = max_output_candidates;
      result["min_separation_px"] = min_separation_px;
      result["catalog_sort_mode"] = grid_catalog_sort_mode(grid_capacity);
      result["catalog_topk_mode"] = grid_catalog_topk_mode(deterministic, candidates_per_cell);
      py::dict centroid_refine = centroid_refine_summary(
          centroid_radius,
          stored_count,
          centroid_before_xs,
          centroid_before_ys,
          static_cast<const float*>(xs_info.ptr),
          static_cast<const float*>(ys_info.ptr),
          centroid_statuses);
      centroid_refine["background_mode"] = centroid_radius > 0 ? centroid_background_mode : "off";
      centroid_refine["mode"] = centroid_radius > 0
          ? (centroid_global_mean_background ? "resident_gpu_global_mean_centroid" : "resident_gpu_window_centroid")
          : "off";
      if (std::isfinite(centroid_background)) {
        centroid_refine["background"] = centroid_background;
      } else {
        centroid_refine["background"] = py::none();
      }
      result["centroid_refine"] = centroid_refine;
      result["x"] = xs[py::slice(0, stored_count, 1)];
      result["y"] = ys[py::slice(0, stored_count, 1)];
      result["flux"] = fluxes[py::slice(0, stored_count, 1)];
      cudaFree(d_grid_xs);
      cudaFree(d_grid_ys);
      cudaFree(d_grid_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      cudaFree(d_refine_status);
      return result;
    } catch (...) {
      cudaFree(d_grid_xs);
      cudaFree(d_grid_ys);
      cudaFree(d_grid_fluxes);
      cudaFree(d_xs);
      cudaFree(d_ys);
      cudaFree(d_fluxes);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      cudaFree(d_refine_status);
      throw;
    }
  }

  py::dict star_grid_top_nms_candidates(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_impl(
        index, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, false);
  }

  py::dict star_grid_top_nms_candidates_centroid(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      int centroid_radius,
      bool centroid_global_mean_background = false) const {
    return star_grid_top_nms_candidates_impl(
        index,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px,
        false,
        centroid_radius,
        centroid_global_mean_background);
  }

  py::dict star_grid_top_nms_candidates_deterministic(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_impl(
        index, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, true);
  }

  py::dict star_grid_top_nms_candidates_deterministic_centroid(
      std::size_t index,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      int centroid_radius,
      bool centroid_global_mean_background = false) const {
    return star_grid_top_nms_candidates_impl(
        index,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px,
        true,
        centroid_radius,
        centroid_global_mean_background);
  }

  py::list star_grid_top_nms_candidates_batch_impl(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      bool deterministic,
      int centroid_radius = 0,
      bool centroid_global_mean_background = false) const {
    if (grid_cols <= 0 || grid_rows <= 0 || candidates_per_cell <= 0 || max_output_candidates <= 0) {
      throw std::invalid_argument("grid dimensions and candidate counts must be positive");
    }
    if (min_separation_px < 0.0f) {
      throw std::invalid_argument("min_separation_px must be non-negative");
    }
    for (const std::size_t index : indices) {
      require_index(index);
      if (!loaded_[index]) {
        throw std::runtime_error("resident frame must be loaded before batched star detection");
      }
    }

    const int cell_count = grid_cols * grid_rows;
    const int grid_capacity = cell_count * candidates_per_cell;
    const std::size_t batch_count = indices.size();
    py::list results;
    if (batch_count == 0) {
      return results;
    }

    const std::size_t grid_stride = static_cast<std::size_t>(grid_capacity);
    const std::size_t out_stride = static_cast<std::size_t>(max_output_candidates);
    float* d_grid_values = nullptr;
    float* d_catalog_values = nullptr;
    float* d_grid_xs = nullptr;
    float* d_grid_ys = nullptr;
    float* d_grid_fluxes = nullptr;
    float* d_xs = nullptr;
    float* d_ys = nullptr;
    float* d_fluxes = nullptr;
    int* d_count = nullptr;
    int* d_locks = nullptr;
    int* d_cell_counts = nullptr;
    int* d_stored_count = nullptr;
    unsigned char* d_refine_status = nullptr;
    double* d_mean_sums = nullptr;
    unsigned int* d_mean_counts = nullptr;
    std::vector<cudaStream_t> catalog_streams;
    std::size_t catalog_stream_count = 0;
    int catalog_sync_phase_count = 1;
    int centroid_mean_blocks = 0;
    bool centroid_global_mean_fused_sync = false;
    try {
      const std::size_t grid_value_count = batch_count * grid_stride;
      const std::size_t catalog_value_count = batch_count * out_stride;
      check_cuda(
          cudaMalloc(&d_grid_values, 3 * grid_value_count * sizeof(float)),
          "cudaMalloc(resident batch grid top nms contiguous grid workspace)");
      d_grid_xs = d_grid_values;
      d_grid_ys = d_grid_values + grid_value_count;
      d_grid_fluxes = d_grid_values + 2 * grid_value_count;
      check_cuda(
          cudaMalloc(&d_catalog_values, 3 * catalog_value_count * sizeof(float)),
          "cudaMalloc(resident batch grid top nms contiguous catalog workspace)");
      d_xs = d_catalog_values;
      d_ys = d_catalog_values + catalog_value_count;
      d_fluxes = d_catalog_values + 2 * catalog_value_count;
      check_cuda(
          cudaMalloc(&d_count, batch_count * sizeof(int)),
          "cudaMalloc(resident batch grid top nms star count)");
      check_cuda(
          cudaMalloc(&d_locks, batch_count * static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident batch grid top nms locks)");
      check_cuda(
          cudaMalloc(&d_cell_counts, batch_count * static_cast<std::size_t>(cell_count) * sizeof(int)),
          "cudaMalloc(resident batch grid top nms cell counts)");
      check_cuda(
          cudaMalloc(&d_stored_count, batch_count * sizeof(int)),
          "cudaMalloc(resident batch grid top nms stored count)");
      if (centroid_radius > 0) {
        check_cuda(
            cudaMalloc(&d_refine_status, batch_count * out_stride * sizeof(unsigned char)),
            "cudaMalloc(resident batch grid top nms centroid status)");
      }
      centroid_global_mean_fused_sync = centroid_radius > 0 && centroid_global_mean_background;
      if (centroid_global_mean_fused_sync) {
        constexpr int mean_threads = 256;
        centroid_mean_blocks = static_cast<int>(
            std::min<std::size_t>(
                4096,
                std::max<std::size_t>(
                    1,
                    (pixels_per_frame_ + static_cast<std::size_t>(mean_threads) - 1) /
                        static_cast<std::size_t>(mean_threads))));
        check_cuda(
            cudaMalloc(
                &d_mean_sums,
                batch_count * static_cast<std::size_t>(centroid_mean_blocks) * sizeof(double)),
            "cudaMalloc(resident batch grid top nms centroid fused mean sums)");
        check_cuda(
            cudaMalloc(
                &d_mean_counts,
                batch_count * static_cast<std::size_t>(centroid_mean_blocks) * sizeof(unsigned int)),
            "cudaMalloc(resident batch grid top nms centroid fused mean counts)");
      }
      constexpr std::size_t catalog_stream_limit = 8;
      catalog_stream_count = std::min<std::size_t>(catalog_stream_limit, batch_count);
      catalog_streams.resize(catalog_stream_count, nullptr);
      for (std::size_t stream_index = 0; stream_index < catalog_stream_count; ++stream_index) {
        check_cuda(
            cudaStreamCreate(&catalog_streams[stream_index]),
            "cudaStreamCreate(resident grid top nms catalog batch stream)");
      }

      const auto enqueue_start = std::chrono::steady_clock::now();
      for (std::size_t batch_pos = 0; batch_pos < batch_count; ++batch_pos) {
        const std::size_t index = indices[batch_pos];
        const std::size_t grid_offset = batch_pos * grid_stride;
        const std::size_t out_offset = batch_pos * out_stride;
        const std::size_t cell_offset = batch_pos * static_cast<std::size_t>(cell_count);
        cudaStream_t stream = catalog_streams[batch_pos % catalog_stream_count];
        if (deterministic) {
          glass_star_grid_top_nms_candidates_deterministic_f32_launch_stream(
              d_stack_ + index * pixels_per_frame_,
              d_grid_xs + grid_offset,
              d_grid_ys + grid_offset,
              d_grid_fluxes + grid_offset,
              d_xs + out_offset,
              d_ys + out_offset,
              d_fluxes + out_offset,
              d_count + batch_pos,
              d_stored_count + batch_pos,
              static_cast<int>(width_),
              static_cast<int>(height_),
              threshold,
              grid_cols,
              grid_rows,
              candidates_per_cell,
              max_output_candidates,
              min_separation_px,
              stream);
        } else {
          glass_star_grid_top_nms_candidates_f32_launch_stream(
              d_stack_ + index * pixels_per_frame_,
              d_grid_xs + grid_offset,
              d_grid_ys + grid_offset,
              d_grid_fluxes + grid_offset,
              d_xs + out_offset,
              d_ys + out_offset,
              d_fluxes + out_offset,
              d_count + batch_pos,
              d_locks + cell_offset,
              d_cell_counts + cell_offset,
              d_stored_count + batch_pos,
              static_cast<int>(width_),
              static_cast<int>(height_),
              threshold,
              grid_cols,
              grid_rows,
              candidates_per_cell,
              max_output_candidates,
              min_separation_px,
              stream);
        }
        if (centroid_global_mean_fused_sync) {
          glass_frame_sum_f32_launch_stream(
              d_stack_ + index * pixels_per_frame_,
              d_mean_sums + batch_pos * static_cast<std::size_t>(centroid_mean_blocks),
              d_mean_counts + batch_pos * static_cast<std::size_t>(centroid_mean_blocks),
              pixels_per_frame_,
              centroid_mean_blocks,
              stream);
        }
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_grid_top_nms_candidates_batch kernel launch");
      const auto enqueue_end = std::chrono::steady_clock::now();
      for (std::size_t stream_index = 0; stream_index < catalog_stream_count; ++stream_index) {
        check_cuda(
            cudaStreamSynchronize(catalog_streams[stream_index]),
            "ResidentCalibratedStack.star_grid_top_nms_candidates_batch stream synchronize");
      }
      const auto sync_end = std::chrono::steady_clock::now();

      std::vector<int> total_counts(batch_count);
      std::vector<int> stored_counts(batch_count);
      check_cuda(
          cudaMemcpy(total_counts.data(), d_count, batch_count * sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident batch grid top nms counts)");
      check_cuda(
          cudaMemcpy(stored_counts.data(), d_stored_count, batch_count * sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident batch grid top nms stored counts)");
      const auto count_download_end = std::chrono::steady_clock::now();

      std::vector<float> centroid_before_xs;
      std::vector<float> centroid_before_ys;
      std::vector<unsigned char> centroid_statuses;
      std::vector<float> centroid_backgrounds(batch_count, std::numeric_limits<float>::quiet_NaN());
      const char* centroid_background_mode = "local_median";
      double centroid_refine_s = 0.0;
      int centroid_before_download_copy_count = 0;
      if (centroid_radius > 0) {
        const auto centroid_start = std::chrono::steady_clock::now();
        std::vector<float> centroid_before_xy(2 * catalog_value_count);
        centroid_statuses.resize(batch_count * out_stride);
        check_cuda(
            cudaMemcpy(
                centroid_before_xy.data(),
                d_catalog_values,
                centroid_before_xy.size() * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms centroid original xy)");
        centroid_before_download_copy_count = 1;
        centroid_before_xs.assign(
            centroid_before_xy.begin(),
            centroid_before_xy.begin() + static_cast<std::ptrdiff_t>(catalog_value_count));
        centroid_before_ys.assign(
            centroid_before_xy.begin() + static_cast<std::ptrdiff_t>(catalog_value_count),
            centroid_before_xy.end());
        if (centroid_global_mean_background) {
          centroid_background_mode = "global_mean";
          std::vector<double> mean_sums(batch_count * static_cast<std::size_t>(centroid_mean_blocks));
          std::vector<unsigned int> mean_counts(batch_count * static_cast<std::size_t>(centroid_mean_blocks));
          check_cuda(
              cudaMemcpy(
                  mean_sums.data(),
                  d_mean_sums,
                  mean_sums.size() * sizeof(double),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident batch grid top nms centroid mean sums)");
          check_cuda(
              cudaMemcpy(
                  mean_counts.data(),
                  d_mean_counts,
                  mean_counts.size() * sizeof(unsigned int),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident batch grid top nms centroid mean counts)");
          for (std::size_t batch_pos = 0; batch_pos < batch_count; ++batch_pos) {
            double sum = 0.0;
            std::size_t count = 0;
            for (int block = 0; block < centroid_mean_blocks; ++block) {
              const std::size_t offset =
                  batch_pos * static_cast<std::size_t>(centroid_mean_blocks) + static_cast<std::size_t>(block);
              sum += mean_sums[offset];
              count += static_cast<std::size_t>(mean_counts[offset]);
            }
            if (count > 0) {
              centroid_backgrounds[batch_pos] = static_cast<float>(sum / static_cast<double>(count));
            }
          }
        }
        ++catalog_sync_phase_count;
        for (std::size_t batch_pos = 0; batch_pos < batch_count; ++batch_pos) {
          const int stored_count = std::max(0, std::min(stored_counts[batch_pos], max_output_candidates));
          if (stored_count <= 0) {
            continue;
          }
          const std::size_t index = indices[batch_pos];
          const std::size_t out_offset = batch_pos * out_stride;
          cudaStream_t stream = catalog_streams[batch_pos % catalog_stream_count];
          glass_star_refine_centroids_f32_launch_stream(
              d_stack_ + index * pixels_per_frame_,
              d_xs + out_offset,
              d_ys + out_offset,
              d_fluxes + out_offset,
              d_refine_status + out_offset,
              stored_count,
              static_cast<int>(width_),
              static_cast<int>(height_),
              centroid_radius,
              centroid_backgrounds[batch_pos],
              stream);
        }
        check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star_grid_top_nms_candidates_batch centroid refine kernel launch");
        for (std::size_t stream_index = 0; stream_index < catalog_stream_count; ++stream_index) {
          check_cuda(
              cudaStreamSynchronize(catalog_streams[stream_index]),
              "ResidentCalibratedStack.star_grid_top_nms_candidates_batch centroid refine stream synchronize");
        }
        check_cuda(
            cudaMemcpy(
                centroid_statuses.data(),
                d_refine_status,
                batch_count * out_stride * sizeof(unsigned char),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident batch grid top nms centroid statuses)");
        centroid_refine_s = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - centroid_start).count();
      }

      std::vector<float> host_catalog_values(3 * catalog_value_count);
      int catalog_output_download_copy_count = 0;
      check_cuda(
          cudaMemcpy(
              host_catalog_values.data(),
              d_catalog_values,
              host_catalog_values.size() * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident batch grid top nms star catalog contiguous soa)");
      catalog_output_download_copy_count = 1;
      const float* host_xs = host_catalog_values.data();
      const float* host_ys = host_xs + catalog_value_count;
      const float* host_fluxes = host_ys + catalog_value_count;
      const auto catalog_download_end = std::chrono::steady_clock::now();

      const double enqueue_s = std::chrono::duration<double>(enqueue_end - enqueue_start).count();
      const double sync_s = std::chrono::duration<double>(sync_end - enqueue_end).count();
      const double count_download_s =
          std::chrono::duration<double>(count_download_end - sync_end).count();
      const double catalog_download_s =
          std::chrono::duration<double>(catalog_download_end - count_download_end).count();
      const double native_s =
          std::chrono::duration<double>(catalog_download_end - enqueue_start).count();
      const double inv_batch = 1.0 / static_cast<double>(batch_count);

      for (std::size_t batch_pos = 0; batch_pos < batch_count; ++batch_pos) {
        const int stored_count = std::max(0, std::min(stored_counts[batch_pos], max_output_candidates));
        const std::size_t out_offset = batch_pos * out_stride;
        py::array_t<float> xs({stored_count});
        py::array_t<float> ys({stored_count});
        py::array_t<float> fluxes({stored_count});
        const py::buffer_info xs_info = xs.request();
        const py::buffer_info ys_info = ys.request();
        const py::buffer_info flux_info = fluxes.request();
        if (stored_count > 0) {
          std::memcpy(
              xs_info.ptr,
              host_xs + out_offset,
              static_cast<std::size_t>(stored_count) * sizeof(float));
          std::memcpy(
              ys_info.ptr,
              host_ys + out_offset,
              static_cast<std::size_t>(stored_count) * sizeof(float));
          std::memcpy(
              flux_info.ptr,
              host_fluxes + out_offset,
              static_cast<std::size_t>(stored_count) * sizeof(float));
        }
        std::vector<float> per_frame_centroid_before_xs;
        std::vector<float> per_frame_centroid_before_ys;
        std::vector<unsigned char> per_frame_centroid_statuses;
        if (centroid_radius > 0 && stored_count > 0) {
          per_frame_centroid_before_xs.assign(
              centroid_before_xs.begin() + static_cast<std::ptrdiff_t>(out_offset),
              centroid_before_xs.begin() + static_cast<std::ptrdiff_t>(out_offset + static_cast<std::size_t>(stored_count)));
          per_frame_centroid_before_ys.assign(
              centroid_before_ys.begin() + static_cast<std::ptrdiff_t>(out_offset),
              centroid_before_ys.begin() + static_cast<std::ptrdiff_t>(out_offset + static_cast<std::size_t>(stored_count)));
          per_frame_centroid_statuses.assign(
              centroid_statuses.begin() + static_cast<std::ptrdiff_t>(out_offset),
              centroid_statuses.begin() + static_cast<std::ptrdiff_t>(out_offset + static_cast<std::size_t>(stored_count)));
        }

        py::dict result;
        result["frame_index"] = indices[batch_pos];
        result["count"] = total_counts[batch_pos];
        result["stored_count"] = stored_count;
        result["grid_cols"] = grid_cols;
        result["grid_rows"] = grid_rows;
        result["candidates_per_cell"] = candidates_per_cell;
        result["max_output_candidates"] = max_output_candidates;
        result["min_separation_px"] = min_separation_px;
        result["catalog_sort_mode"] = grid_catalog_sort_mode(grid_capacity);
        result["catalog_topk_mode"] = grid_catalog_topk_mode(deterministic, candidates_per_cell);
        result["catalog_timing_model"] = centroid_radius > 0
            ? (centroid_global_mean_background
                   ? "batch_multistream_bulk_download_centroid_global_mean_fused_sync"
                   : "batch_multistream_bulk_download_centroid_multistream")
            : "batch_multistream_bulk_download";
        result["catalog_batch_size"] = static_cast<int>(batch_count);
        result["catalog_stream_limit"] = static_cast<int>(catalog_stream_limit);
        result["catalog_stream_count"] = static_cast<int>(catalog_stream_count);
        result["catalog_batch_sync_count"] = static_cast<int>(catalog_stream_count);
        result["catalog_sync_phase_count"] = catalog_sync_phase_count;
        result["catalog_download_mode"] = "bulk_full_capacity";
        result["catalog_workspace_layout"] = "contiguous_soa";
        result["catalog_grid_workspace_allocation_count"] = 1;
        result["catalog_output_workspace_allocation_count"] = 1;
        result["catalog_output_download_copy_count"] = catalog_output_download_copy_count;
        result["catalog_centroid_before_download_copy_count"] = centroid_before_download_copy_count;
        result["catalog_output_download_bytes"] =
            static_cast<unsigned long long>(host_catalog_values.size() * sizeof(float));
        result["catalog_centroid_mean_sync_mode"] = centroid_global_mean_background
            ? "fused_with_catalog_sync"
            : (centroid_radius > 0 ? "not_applicable_local_median" : "off");
        result["catalog_centroid_mean_blocks"] = centroid_mean_blocks;
        result["catalog_enqueue_s"] = enqueue_s * inv_batch;
        result["catalog_sync_s"] = sync_s * inv_batch;
        result["catalog_count_download_s"] = count_download_s * inv_batch;
        result["catalog_centroid_refine_s"] = centroid_refine_s * inv_batch;
        result["catalog_output_download_s"] = catalog_download_s * inv_batch;
        result["catalog_native_s"] = native_s * inv_batch;
        py::dict centroid_refine = centroid_refine_summary(
            centroid_radius,
            stored_count,
            per_frame_centroid_before_xs,
            per_frame_centroid_before_ys,
            static_cast<const float*>(xs_info.ptr),
            static_cast<const float*>(ys_info.ptr),
            per_frame_centroid_statuses);
        centroid_refine["background_mode"] = centroid_radius > 0 ? centroid_background_mode : "off";
        centroid_refine["mode"] = centroid_radius > 0
            ? (centroid_global_mean_background ? "resident_gpu_global_mean_centroid" : "resident_gpu_window_centroid")
            : "off";
        if (centroid_radius > 0 && std::isfinite(centroid_backgrounds[batch_pos])) {
          centroid_refine["background"] = centroid_backgrounds[batch_pos];
        } else {
          centroid_refine["background"] = py::none();
        }
        result["centroid_refine"] = centroid_refine;
        result["x"] = xs[py::slice(0, stored_count, 1)];
        result["y"] = ys[py::slice(0, stored_count, 1)];
        result["flux"] = fluxes[py::slice(0, stored_count, 1)];
        results.append(result);
      }

      cudaFree(d_grid_values);
      cudaFree(d_catalog_values);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      cudaFree(d_refine_status);
      cudaFree(d_mean_sums);
      cudaFree(d_mean_counts);
      for (cudaStream_t stream : catalog_streams) {
        if (stream != nullptr) {
          cudaStreamDestroy(stream);
        }
      }
      return results;
    } catch (...) {
      for (cudaStream_t stream : catalog_streams) {
        if (stream != nullptr) {
          (void)cudaStreamSynchronize(stream);
          (void)cudaStreamDestroy(stream);
        }
      }
      cudaFree(d_grid_values);
      cudaFree(d_catalog_values);
      cudaFree(d_count);
      cudaFree(d_locks);
      cudaFree(d_cell_counts);
      cudaFree(d_stored_count);
      cudaFree(d_refine_status);
      cudaFree(d_mean_sums);
      cudaFree(d_mean_counts);
      throw;
    }
  }

  py::list star_grid_top_nms_candidates_batch(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_batch_impl(
        indices, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, false);
  }

  py::list star_grid_top_nms_candidates_batch_centroid(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      int centroid_radius,
      bool centroid_global_mean_background = false) const {
    return star_grid_top_nms_candidates_batch_impl(
        indices,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px,
        false,
        centroid_radius,
        centroid_global_mean_background);
  }

  py::list star_grid_top_nms_candidates_batch_deterministic(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px) const {
    return star_grid_top_nms_candidates_batch_impl(
        indices, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px, true);
  }

  py::list star_grid_top_nms_candidates_batch_deterministic_centroid(
      const std::vector<std::size_t>& indices,
      float threshold,
      int grid_cols,
      int grid_rows,
      int candidates_per_cell,
      int max_output_candidates,
      float min_separation_px,
      int centroid_radius,
      bool centroid_global_mean_background = false) const {
    return star_grid_top_nms_candidates_batch_impl(
        indices,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px,
        true,
        centroid_radius,
        centroid_global_mean_background);
  }

  py::dict estimate_translation_from_stars_to_reference(
      std::size_t reference_index,
      std::size_t moving_index,
      float threshold,
      int max_candidates,
      float tolerance_px,
      float max_abs_dx,
      float max_abs_dy,
      float prior_dx,
      float prior_dy,
      float prior_radius_px,
      int grid_cols,
      int grid_rows) const {
    require_loaded(reference_index, "resident star-catalog reference registration");
    require_loaded(moving_index, "resident star-catalog moving registration");
    if (max_candidates <= 0) {
      throw std::invalid_argument("max_candidates must be positive");
    }
    if (tolerance_px < 0.0f) {
      throw std::invalid_argument("tolerance_px must be non-negative");
    }
    if (max_abs_dx < 0.0f) {
      max_abs_dx = -1.0f;
    }
    if (max_abs_dy < 0.0f) {
      max_abs_dy = max_abs_dx;
    }
    if (prior_radius_px < 0.0f) {
      prior_radius_px = -1.0f;
    }
    const bool use_grid_candidates = grid_cols > 0 || grid_rows > 0;
    if (use_grid_candidates && (grid_cols <= 0 || grid_rows <= 0)) {
      throw std::invalid_argument("resident star grid dimensions must both be positive");
    }
    const int catalog_capacity = use_grid_candidates ? grid_cols * grid_rows : max_candidates;

    float* d_reference_x = nullptr;
    float* d_reference_y = nullptr;
    float* d_reference_flux = nullptr;
    float* d_moving_x = nullptr;
    float* d_moving_y = nullptr;
    float* d_moving_flux = nullptr;
    int* d_reference_count = nullptr;
    int* d_moving_count = nullptr;
    int* d_reference_lock = nullptr;
    int* d_moving_lock = nullptr;
    float* d_candidate_dx = nullptr;
    float* d_candidate_dy = nullptr;
    int* d_scores = nullptr;
    float* d_best_dx = nullptr;
    float* d_best_dy = nullptr;
    int* d_best_inliers = nullptr;
    int* d_moving_best_reference = nullptr;
    int* d_reference_best_moving = nullptr;
    float* d_refine_sums = nullptr;
    int* d_mutual_inliers = nullptr;
    float* d_refined_dx = nullptr;
    float* d_refined_dy = nullptr;
    float* d_rms_px = nullptr;
    int reference_total_count = 0;
    int moving_total_count = 0;
    float best_dx = 0.0f;
    float best_dy = 0.0f;
    int best_inliers = 0;
    int mutual_inliers = 0;
    float refined_dx = 0.0f;
    float refined_dy = 0.0f;
    float rms_px = 0.0f;

    try {
      const std::size_t catalog_bytes = static_cast<std::size_t>(catalog_capacity) * sizeof(float);
      check_cuda(cudaMalloc(&d_reference_x, catalog_bytes), "cudaMalloc(resident reference star xs)");
      check_cuda(cudaMalloc(&d_reference_y, catalog_bytes), "cudaMalloc(resident reference star ys)");
      check_cuda(cudaMalloc(&d_reference_flux, catalog_bytes), "cudaMalloc(resident reference star flux)");
      check_cuda(cudaMalloc(&d_moving_x, catalog_bytes), "cudaMalloc(resident moving star xs)");
      check_cuda(cudaMalloc(&d_moving_y, catalog_bytes), "cudaMalloc(resident moving star ys)");
      check_cuda(cudaMalloc(&d_moving_flux, catalog_bytes), "cudaMalloc(resident moving star flux)");
      check_cuda(cudaMalloc(&d_reference_count, sizeof(int)), "cudaMalloc(resident reference star count)");
      check_cuda(cudaMalloc(&d_moving_count, sizeof(int)), "cudaMalloc(resident moving star count)");
      const std::size_t lock_count = use_grid_candidates ? static_cast<std::size_t>(catalog_capacity) : 1ULL;
      check_cuda(cudaMalloc(&d_reference_lock, lock_count * sizeof(int)), "cudaMalloc(resident reference star locks)");
      check_cuda(cudaMalloc(&d_moving_lock, lock_count * sizeof(int)), "cudaMalloc(resident moving star locks)");
      if (use_grid_candidates) {
        glass_star_grid_candidates_f32_launch(
            d_stack_ + reference_index * pixels_per_frame_,
            d_reference_x,
            d_reference_y,
            d_reference_flux,
            d_reference_count,
            d_reference_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows);
        glass_star_grid_candidates_f32_launch(
            d_stack_ + moving_index * pixels_per_frame_,
            d_moving_x,
            d_moving_y,
            d_moving_flux,
            d_moving_count,
            d_moving_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            grid_cols,
            grid_rows);
      } else {
        glass_star_top_candidates_f32_launch(
            d_stack_ + reference_index * pixels_per_frame_,
            d_reference_x,
            d_reference_y,
            d_reference_flux,
            d_reference_count,
            d_reference_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            max_candidates);
        glass_star_top_candidates_f32_launch(
            d_stack_ + moving_index * pixels_per_frame_,
            d_moving_x,
            d_moving_y,
            d_moving_flux,
            d_moving_count,
            d_moving_lock,
            static_cast<int>(width_),
            static_cast<int>(height_),
            threshold,
            max_candidates);
      }
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star-catalog detection kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star-catalog detection synchronize");
      check_cuda(
          cudaMemcpy(&reference_total_count, d_reference_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident reference star count)");
      check_cuda(
          cudaMemcpy(&moving_total_count, d_moving_count, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident moving star count)");
      const int reference_count = std::min(reference_total_count, catalog_capacity);
      const int moving_count = std::min(moving_total_count, catalog_capacity);
      if (reference_count <= 0 || moving_count <= 0) {
        throw std::runtime_error("resident star-catalog registration found no stars");
      }
      const int pair_count = reference_count * moving_count;
      check_cuda(
          cudaMalloc(&d_candidate_dx, static_cast<std::size_t>(pair_count) * sizeof(float)),
          "cudaMalloc(resident catalog candidate dx)");
      check_cuda(
          cudaMalloc(&d_candidate_dy, static_cast<std::size_t>(pair_count) * sizeof(float)),
          "cudaMalloc(resident catalog candidate dy)");
      check_cuda(
          cudaMalloc(&d_scores, static_cast<std::size_t>(pair_count) * sizeof(int)),
          "cudaMalloc(resident catalog scores)");
      check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(resident catalog best dx)");
      check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(resident catalog best dy)");
      check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(resident catalog best inliers)");
      check_cuda(
          cudaMalloc(&d_moving_best_reference, static_cast<std::size_t>(moving_count) * sizeof(int)),
          "cudaMalloc(resident catalog moving best reference)");
      check_cuda(
          cudaMalloc(&d_reference_best_moving, static_cast<std::size_t>(reference_count) * sizeof(int)),
          "cudaMalloc(resident catalog reference best moving)");
      check_cuda(cudaMalloc(&d_refine_sums, 3 * sizeof(float)), "cudaMalloc(resident catalog refine sums)");
      check_cuda(cudaMalloc(&d_mutual_inliers, sizeof(int)), "cudaMalloc(resident catalog mutual inliers)");
      check_cuda(cudaMalloc(&d_refined_dx, sizeof(float)), "cudaMalloc(resident catalog refined dx)");
      check_cuda(cudaMalloc(&d_refined_dy, sizeof(float)), "cudaMalloc(resident catalog refined dy)");
      check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(resident catalog rms)");
      glass_estimate_translation_from_catalogs_f32_launch(
          d_reference_x,
          d_reference_y,
          d_moving_x,
          d_moving_y,
          d_candidate_dx,
          d_candidate_dy,
          d_scores,
          d_best_dx,
          d_best_dy,
          d_best_inliers,
          d_moving_best_reference,
          d_reference_best_moving,
          d_refine_sums,
          d_mutual_inliers,
          d_refined_dx,
          d_refined_dy,
          d_rms_px,
          reference_count,
          moving_count,
          tolerance_px,
          max_abs_dx,
          max_abs_dy,
          prior_dx,
          prior_dy,
          prior_radius_px);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.star-catalog translation kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.star-catalog translation synchronize");
      check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog best dx)");
      check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog best dy)");
      check_cuda(
          cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident catalog best inliers)");
      check_cuda(
          cudaMemcpy(&mutual_inliers, d_mutual_inliers, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident catalog mutual inliers)");
      check_cuda(cudaMemcpy(&refined_dx, d_refined_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog refined dx)");
      check_cuda(cudaMemcpy(&refined_dy, d_refined_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog refined dy)");
      check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(resident catalog rms)");
    } catch (...) {
      cudaFree(d_reference_x);
      cudaFree(d_reference_y);
      cudaFree(d_reference_flux);
      cudaFree(d_moving_x);
      cudaFree(d_moving_y);
      cudaFree(d_moving_flux);
      cudaFree(d_reference_count);
      cudaFree(d_moving_count);
      cudaFree(d_reference_lock);
      cudaFree(d_moving_lock);
      cudaFree(d_candidate_dx);
      cudaFree(d_candidate_dy);
      cudaFree(d_scores);
      cudaFree(d_best_dx);
      cudaFree(d_best_dy);
      cudaFree(d_best_inliers);
      cudaFree(d_moving_best_reference);
      cudaFree(d_reference_best_moving);
      cudaFree(d_refine_sums);
      cudaFree(d_mutual_inliers);
      cudaFree(d_refined_dx);
      cudaFree(d_refined_dy);
      cudaFree(d_rms_px);
      throw;
    }
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_reference_flux);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_moving_flux);
    cudaFree(d_reference_count);
    cudaFree(d_moving_count);
    cudaFree(d_reference_lock);
    cudaFree(d_moving_lock);
    cudaFree(d_candidate_dx);
    cudaFree(d_candidate_dy);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_inliers);
    cudaFree(d_moving_best_reference);
    cudaFree(d_reference_best_moving);
    cudaFree(d_refine_sums);
    cudaFree(d_mutual_inliers);
    cudaFree(d_refined_dx);
    cudaFree(d_refined_dy);
    cudaFree(d_rms_px);

    const int reference_count = std::min(reference_total_count, catalog_capacity);
    const int moving_count = std::min(moving_total_count, catalog_capacity);
    py::dict result;
    result["dx"] = best_dx;
    result["dy"] = best_dy;
    result["inliers"] = best_inliers;
    result["refined_dx"] = refined_dx;
    result["refined_dy"] = refined_dy;
    result["mutual_inliers"] = mutual_inliers;
    result["rms_px"] = rms_px;
    result["candidate_count"] = reference_count * moving_count;
    result["reference_count"] = reference_count;
    result["moving_count"] = moving_count;
    result["reference_total_count"] = reference_total_count;
    result["moving_total_count"] = moving_total_count;
    result["threshold"] = threshold;
    result["max_candidates"] = max_candidates;
    result["catalog_capacity"] = catalog_capacity;
    result["candidate_selection"] = use_grid_candidates ? "grid_brightest_per_cell" : "top_flux";
    result["grid_cols"] = grid_cols;
    result["grid_rows"] = grid_rows;
    result["tolerance_px"] = tolerance_px;
    result["max_abs_dx"] = max_abs_dx;
    result["max_abs_dy"] = max_abs_dy;
    result["prior_dx"] = prior_dx;
    result["prior_dy"] = prior_dy;
    result["prior_radius_px"] = prior_radius_px;
    result["reference_index"] = reference_index;
    result["moving_index"] = moving_index;
    result["model"] = "resident_star_catalog_pair_offset_translation";
    return result;
  }

  py::tuple integrate_mean(py::object weights_obj) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    const py::buffer_info weight_map_info = weight_map.request();

    float* d_weights = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    try {
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(resident weights)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident master)");
      check_cuda(cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident weight map)");
      check_cuda(
          cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident weights)");
      glass_integrate_resident_weighted_mean_f32_launch(
          d_stack_,
          d_weights,
          d_master,
          d_weight_map,
          frame_count_,
          pixels_per_frame_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_mean kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_mean synchronize");
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident master)");
      check_cuda(
          cudaMemcpy(
              weight_map_info.ptr,
              d_weight_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident weight map)");
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    return py::make_tuple(master, weight_map);
  }

  py::tuple integrate_tile_local_mean(
      py::object target_mask_obj,
      py::object tile_extents_obj,
      py::object tile_multipliers_obj,
      py::object weights_obj) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }
    if (width_ > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        height_ > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("resident tile-local integration requires image dimensions within int range");
    }

    const auto total_start = Clock::now();
    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    auto target_mask_array =
        py::cast<py::array_t<unsigned char, py::array::c_style | py::array::forcecast>>(target_mask_obj);
    const py::buffer_info target_mask_info = target_mask_array.request();
    if (target_mask_info.ndim != 1 ||
        static_cast<std::size_t>(target_mask_info.shape[0]) != frame_count_) {
      throw std::invalid_argument("target_mask must have shape (frame_count,)");
    }
    const auto* target_mask_ptr = static_cast<const unsigned char*>(target_mask_info.ptr);
    std::vector<unsigned char> target_mask(target_mask_ptr, target_mask_ptr + frame_count_);
    std::size_t target_frame_count = 0;
    for (const unsigned char value : target_mask) {
      if (value != 0) {
        ++target_frame_count;
      }
    }
    if (target_frame_count == 0) {
      throw std::invalid_argument("target_mask must select at least one resident frame");
    }

    auto tile_extents_array =
        py::cast<py::array_t<int, py::array::c_style | py::array::forcecast>>(tile_extents_obj);
    const py::buffer_info tile_extents_info = tile_extents_array.request();
    if (tile_extents_info.ndim != 2 || tile_extents_info.shape[1] != 4) {
      throw std::invalid_argument("tile_extents must have shape (tile_count, 4)");
    }
    const std::size_t tile_count = static_cast<std::size_t>(tile_extents_info.shape[0]);
    if (tile_count == 0 || tile_count > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("tile_extents must contain between 1 and INT_MAX tiles");
    }
    const auto* tile_extents_ptr = static_cast<const int*>(tile_extents_info.ptr);
    std::vector<int> tile_extents(tile_extents_ptr, tile_extents_ptr + tile_count * 4);

    auto tile_multipliers_array =
        py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(tile_multipliers_obj);
    const py::buffer_info tile_multipliers_info = tile_multipliers_array.request();
    if (tile_multipliers_info.ndim != 1 ||
        static_cast<std::size_t>(tile_multipliers_info.shape[0]) != tile_count) {
      throw std::invalid_argument("tile_multipliers must have shape (tile_count,)");
    }
    const auto* tile_multipliers_ptr = static_cast<const float*>(tile_multipliers_info.ptr);
    std::vector<float> tile_multipliers(tile_multipliers_ptr, tile_multipliers_ptr + tile_count);

    for (std::size_t tile = 0; tile < tile_count; ++tile) {
      const int base = static_cast<int>(tile * 4);
      const int x0 = tile_extents[base + 0];
      const int y0 = tile_extents[base + 1];
      const int x1 = tile_extents[base + 2];
      const int y1 = tile_extents[base + 3];
      if (x0 < 0 || y0 < 0 || x1 <= x0 || y1 <= y0 ||
          x1 > static_cast<int>(width_) || y1 > static_cast<int>(height_)) {
        throw std::invalid_argument("tile_extents must be positive half-open rectangles inside the image");
      }
      const float multiplier = tile_multipliers[tile];
      if (!std::isfinite(multiplier) || multiplier < 0.0f) {
        throw std::invalid_argument("tile_multipliers must be finite non-negative values");
      }
    }
    for (std::size_t left = 0; left < tile_count; ++left) {
      const int left_base = static_cast<int>(left * 4);
      const int left_x0 = tile_extents[left_base + 0];
      const int left_y0 = tile_extents[left_base + 1];
      const int left_x1 = tile_extents[left_base + 2];
      const int left_y1 = tile_extents[left_base + 3];
      for (std::size_t right = left + 1; right < tile_count; ++right) {
        const int right_base = static_cast<int>(right * 4);
        const int right_x0 = tile_extents[right_base + 0];
        const int right_y0 = tile_extents[right_base + 1];
        const int right_x1 = tile_extents[right_base + 2];
        const int right_y1 = tile_extents[right_base + 3];
        if (std::max(left_x0, right_x0) < std::min(left_x1, right_x1) &&
            std::max(left_y0, right_y0) < std::min(left_y1, right_y1)) {
          throw std::invalid_argument("tile_extents must not overlap for deterministic tile-local integration");
        }
      }
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    const py::buffer_info weight_map_info = weight_map.request();

    float* d_weights = nullptr;
    unsigned char* d_target_mask = nullptr;
    int* d_tile_extents = nullptr;
    float* d_tile_multipliers = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    double device_alloc_s = 0.0;
    double weights_upload_s = 0.0;
    double policy_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(resident tile-local weights)");
      check_cuda(
          cudaMalloc(&d_target_mask, frame_count_ * sizeof(unsigned char)),
          "cudaMalloc(resident tile-local target mask)");
      check_cuda(
          cudaMalloc(&d_tile_extents, tile_count * 4 * sizeof(int)),
          "cudaMalloc(resident tile-local extents)");
      check_cuda(
          cudaMalloc(&d_tile_multipliers, tile_count * sizeof(float)),
          "cudaMalloc(resident tile-local multipliers)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident tile-local master)");
      check_cuda(
          cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident tile-local weight map)");
      device_alloc_s = seconds_since(alloc_start);

      const auto weights_upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local weights)");
      weights_upload_s = seconds_since(weights_upload_start);

      const auto policy_upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_target_mask, target_mask.data(), frame_count_ * sizeof(unsigned char), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local target mask)");
      check_cuda(
          cudaMemcpy(d_tile_extents, tile_extents.data(), tile_count * 4 * sizeof(int), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local extents)");
      check_cuda(
          cudaMemcpy(
              d_tile_multipliers,
              tile_multipliers.data(),
              tile_count * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local multipliers)");
      policy_upload_s = seconds_since(policy_upload_start);

      const auto kernel_start = Clock::now();
      glass_integrate_resident_tile_local_weighted_mean_f32_launch(
          d_stack_,
          d_weights,
          d_target_mask,
          d_tile_extents,
          d_tile_multipliers,
          d_master,
          d_weight_map,
          frame_count_,
          static_cast<int>(width_),
          static_cast<int>(height_),
          static_cast<int>(tile_count));
      kernel_enqueue_s = seconds_since(kernel_start);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_tile_local_mean kernel launch");
      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_tile_local_mean synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local master)");
      check_cuda(
          cudaMemcpy(
              weight_map_info.ptr,
              d_weight_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local weight map)");
      download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_target_mask);
      cudaFree(d_tile_extents);
      cudaFree(d_tile_multipliers);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_target_mask);
    cudaFree(d_tile_extents);
    cudaFree(d_tile_multipliers);
    cudaFree(d_master);
    cudaFree(d_weight_map);

    py::dict timing;
    timing["schema_version"] = 1;
    timing["timing_model"] = "native_resident_tile_local_weighted_mean_one_sync";
    timing["rejection"] = "none";
    timing["frame_count"] = static_cast<unsigned long long>(frame_count_);
    timing["target_frame_count"] = static_cast<unsigned long long>(target_frame_count);
    timing["tile_count"] = static_cast<unsigned long long>(tile_count);
    timing["device_alloc_s"] = device_alloc_s;
    timing["weights_upload_s"] = weights_upload_s;
    timing["policy_upload_s"] = policy_upload_s;
    timing["kernel_enqueue_s"] = kernel_enqueue_s;
    timing["sync_s"] = sync_s;
    timing["download_s"] = download_s;
    timing["total_s"] = seconds_since(total_start);
    timing["weights_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(float));
    timing["target_mask_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(unsigned char));
    timing["tile_extents_bytes"] = static_cast<unsigned long long>(tile_count * 4 * sizeof(int));
    timing["tile_multipliers_bytes"] = static_cast<unsigned long long>(tile_count * sizeof(float));
    timing["output_bytes"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float) * 2);
    timing["modifies_resident_stack"] = false;
    return py::make_tuple(master, weight_map, timing);
  }

  py::tuple integrate_sigma_clip(
      py::object weights_obj,
      float low_sigma,
      float high_sigma,
      bool winsorize,
      const std::string& download_mode = "full") const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }
    if (low_sigma <= 0.0f || high_sigma <= 0.0f) {
      throw std::invalid_argument("sigma thresholds must be positive");
    }
    if (download_mode != "full" && download_mode != "master_weight" && download_mode != "master_only") {
      throw std::invalid_argument("download_mode must be full, master_weight, or master_only");
    }
    const bool download_diagnostics = download_mode == "full";
    const bool download_weight_map = download_mode != "master_only";

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map;
    py::array_t<float> coverage_map;
    py::array_t<float> low_rejection_map;
    py::array_t<float> high_rejection_map;
    if (download_diagnostics) {
      coverage_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      low_rejection_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      high_rejection_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    }
    const py::buffer_info master_info = master.request();
    py::object weight_obj = py::none();
    py::object coverage_obj = py::none();
    py::object low_obj = py::none();
    py::object high_obj = py::none();
    float* weight_ptr = nullptr;
    float* coverage_ptr = nullptr;
    float* low_ptr = nullptr;
    float* high_ptr = nullptr;
    if (download_weight_map) {
      weight_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info weight_map_info = weight_map.request();
      weight_ptr = static_cast<float*>(weight_map_info.ptr);
      weight_obj = weight_map;
    }
    if (download_diagnostics) {
      const py::buffer_info coverage_info = coverage_map.request();
      const py::buffer_info low_info = low_rejection_map.request();
      const py::buffer_info high_info = high_rejection_map.request();
      coverage_ptr = static_cast<float*>(coverage_info.ptr);
      low_ptr = static_cast<float*>(low_info.ptr);
      high_ptr = static_cast<float*>(high_info.ptr);
      coverage_obj = coverage_map;
      low_obj = low_rejection_map;
      high_obj = high_rejection_map;
    }

    float* d_weights = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    float* d_coverage_map = nullptr;
    float* d_low_rejection_map = nullptr;
    float* d_high_rejection_map = nullptr;
    try {
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(resident sigma weights)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident sigma master)");
      if (download_weight_map) {
        check_cuda(
            cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident sigma weight map)");
      }
      if (download_diagnostics) {
        check_cuda(
            cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident sigma coverage map)");
        check_cuda(
            cudaMalloc(&d_low_rejection_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident sigma low rejection map)");
        check_cuda(
            cudaMalloc(&d_high_rejection_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident sigma high rejection map)");
      }
      check_cuda(
          cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident sigma weights)");
      glass_integrate_resident_sigma_clip_f32_launch(
          d_stack_,
          d_weights,
          d_master,
          d_weight_map,
          d_coverage_map,
          d_low_rejection_map,
          d_high_rejection_map,
          frame_count_,
          pixels_per_frame_,
          low_sigma,
          high_sigma,
          winsorize);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_sigma_clip kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_sigma_clip synchronize");
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident sigma master)");
      if (download_weight_map) {
        check_cuda(
            cudaMemcpy(
                weight_ptr,
                d_weight_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident sigma weight map)");
      }
      if (download_diagnostics) {
        check_cuda(
            cudaMemcpy(
                coverage_ptr,
                d_coverage_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident sigma coverage map)");
        check_cuda(
            cudaMemcpy(
                low_ptr,
                d_low_rejection_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident sigma low rejection map)");
        check_cuda(
            cudaMemcpy(
                high_ptr,
                d_high_rejection_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident sigma high rejection map)");
      }
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_low_rejection_map);
      cudaFree(d_high_rejection_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_low_rejection_map);
    cudaFree(d_high_rejection_map);
    return py::make_tuple(
        master,
        weight_obj,
        coverage_obj,
        low_obj,
        high_obj);
  }

  py::tuple integrate_hardened_winsorized_sigma(
      py::object weights_obj,
      float low_sigma,
      float high_sigma,
      int min_samples,
      float max_reject_fraction,
      const std::string& count_map_dtype,
      bool profile,
      const std::string& download_mode = "full") const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }
    if (low_sigma <= 0.0f || high_sigma <= 0.0f) {
      throw std::invalid_argument("sigma thresholds must be positive");
    }
    if (min_samples < 1) {
      throw std::invalid_argument("min_samples must be at least 1");
    }
    if (max_reject_fraction < 0.0f || max_reject_fraction > 1.0f) {
      throw std::invalid_argument("max_reject_fraction must be between 0 and 1");
    }
    if (count_map_dtype != "float32" && count_map_dtype != "uint16") {
      throw std::invalid_argument("count_map_dtype must be float32 or uint16");
    }
    if (download_mode != "full" && download_mode != "master_weight" && download_mode != "master_only") {
      throw std::invalid_argument("download_mode must be full, master_weight, or master_only");
    }
    const bool download_diagnostics = download_mode == "full";
    const bool download_weight_map = download_mode != "master_only";

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }
    bool unit_positive_weights = true;
    std::size_t unit_positive_weight_frame_count = 0;
    for (const float weight : weights) {
      if (std::isfinite(weight) && weight > 0.0f) {
        ++unit_positive_weight_frame_count;
      }
      if (std::isfinite(weight) && weight > 0.0f && weight != 1.0f) {
        unit_positive_weights = false;
      }
    }
    std::string unit_active_index_env_value;
    std::string unit_local_reuse_env_value;
    std::string radix_select_env_value;
#ifdef _MSC_VER
    char* unit_active_index_env_buffer = nullptr;
    std::size_t unit_active_index_env_length = 0;
    if (_dupenv_s(
            &unit_active_index_env_buffer,
            &unit_active_index_env_length,
            "GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX") == 0 &&
        unit_active_index_env_buffer != nullptr) {
      unit_active_index_env_value = unit_active_index_env_buffer;
      std::free(unit_active_index_env_buffer);
    }
    char* unit_local_reuse_env_buffer = nullptr;
    std::size_t unit_local_reuse_env_length = 0;
    if (_dupenv_s(
            &unit_local_reuse_env_buffer,
            &unit_local_reuse_env_length,
            "GLASS_CUDA_UNIT_WEIGHT_LOCAL_REUSE") == 0 &&
        unit_local_reuse_env_buffer != nullptr) {
      unit_local_reuse_env_value = unit_local_reuse_env_buffer;
      std::free(unit_local_reuse_env_buffer);
    }
    char* radix_select_env_buffer = nullptr;
    std::size_t radix_select_env_length = 0;
    if (_dupenv_s(
            &radix_select_env_buffer,
            &radix_select_env_length,
            "GLASS_CUDA_RADIX_SELECT_WINSORIZED") == 0 &&
        radix_select_env_buffer != nullptr) {
      radix_select_env_value = radix_select_env_buffer;
      std::free(radix_select_env_buffer);
    }
#else
    const char* unit_active_index_env = std::getenv("GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX");
    if (unit_active_index_env != nullptr) {
      unit_active_index_env_value = unit_active_index_env;
    }
    const char* unit_local_reuse_env = std::getenv("GLASS_CUDA_UNIT_WEIGHT_LOCAL_REUSE");
    if (unit_local_reuse_env != nullptr) {
      unit_local_reuse_env_value = unit_local_reuse_env;
    }
    const char* radix_select_env = std::getenv("GLASS_CUDA_RADIX_SELECT_WINSORIZED");
    if (radix_select_env != nullptr) {
      radix_select_env_value = radix_select_env;
    }
#endif
    const bool radix_select_requested =
        !radix_select_env_value.empty() && radix_select_env_value != "0" &&
        radix_select_env_value != "false" && radix_select_env_value != "FALSE";
    const bool radix_select_enabled =
        radix_select_requested && unit_positive_weight_frame_count > 512;
    if (unit_positive_weight_frame_count == 0) {
      throw std::invalid_argument(
          "hardened resident winsorized sigma requires at least one positive-weight resident frame");
    }
    if (unit_positive_weight_frame_count > 512 && !radix_select_enabled) {
      throw std::invalid_argument(
          "hardened resident winsorized sigma currently supports at most 512 positive-weight resident frames");
    }
    const bool unit_positive_active_index_requested =
        !radix_select_enabled && unit_positive_weights &&
        !unit_active_index_env_value.empty() && unit_active_index_env_value != "0" &&
        unit_active_index_env_value != "false" && unit_active_index_env_value != "FALSE";
    const bool unit_positive_active_count_admission =
        !radix_select_enabled && unit_positive_weights && frame_count_ > 512 &&
        unit_positive_weight_frame_count <= 512;
    const bool unit_positive_active_index_enabled =
        unit_positive_active_index_requested || unit_positive_active_count_admission;
    const bool unit_positive_local_reuse_requested =
        !radix_select_enabled && unit_positive_weights &&
        !unit_local_reuse_env_value.empty() && unit_local_reuse_env_value != "0" &&
        unit_local_reuse_env_value != "false" && unit_local_reuse_env_value != "FALSE";
    const bool unit_positive_local_reuse_enabled =
        unit_positive_local_reuse_requested && !unit_positive_active_index_enabled;
    const std::string unit_mask_scan_env_value =
        glass_get_env_string("GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN");
    const bool unit_positive_weight_mask_env_enabled =
        glass_env_flag_enabled_strict(unit_mask_scan_env_value);
    const std::string unit_positive_weight_mask_env_reason =
        glass_env_flag_reason_strict(unit_mask_scan_env_value);
    const bool unit_positive_weight_mask_default_enabled =
        unit_mask_scan_env_value.empty();
    const bool unit_positive_weight_mask_policy_enabled =
        unit_positive_weight_mask_default_enabled || unit_positive_weight_mask_env_enabled;
    const std::string unit_positive_weight_mask_policy_source =
        unit_positive_weight_mask_default_enabled
            ? "default_unit_positive_weight_mask_scan"
            : unit_positive_weight_mask_env_reason;
    const bool unit_positive_weight_mask_blocked_by_precedence =
        unit_positive_active_index_enabled || unit_positive_local_reuse_enabled;
    const bool unit_positive_weight_mask_requested =
        !radix_select_enabled && unit_positive_weights &&
        !unit_positive_weight_mask_blocked_by_precedence &&
        unit_positive_weight_mask_policy_enabled;
    const bool unit_positive_weight_mask_enabled = unit_positive_weight_mask_requested;
    const std::string unit_selected_reuse_env_value =
        glass_get_env_string("GLASS_CUDA_UNIT_WEIGHT_SELECTED_REUSE");
    const bool unit_positive_selected_reuse_env_enabled =
        glass_env_flag_enabled_strict(unit_selected_reuse_env_value);
    const std::string unit_positive_selected_reuse_reason =
        glass_env_flag_reason_strict(unit_selected_reuse_env_value);
    const bool unit_positive_selected_reuse_requested =
        !unit_selected_reuse_env_value.empty() && unit_positive_selected_reuse_env_enabled;
    const bool unit_positive_selected_reuse_enabled =
        unit_positive_selected_reuse_requested && !radix_select_enabled &&
        unit_positive_weights && unit_positive_weight_mask_enabled &&
        !unit_positive_active_index_enabled && !unit_positive_local_reuse_enabled;
    std::string unit_positive_weight_mask_reason = unit_positive_weight_mask_policy_source;
    if (unit_positive_weight_mask_enabled) {
      unit_positive_weight_mask_reason = unit_positive_weight_mask_policy_source;
    } else if (!unit_positive_weight_mask_policy_enabled) {
      unit_positive_weight_mask_reason = unit_positive_weight_mask_policy_source;
    } else if (radix_select_enabled) {
      unit_positive_weight_mask_reason = "disabled_by_radix_select";
    } else if (!unit_positive_weights) {
      unit_positive_weight_mask_reason = "disabled_non_unit_weights";
    } else if (unit_positive_weight_mask_blocked_by_precedence &&
               unit_positive_weight_mask_policy_enabled) {
      unit_positive_weight_mask_reason = "disabled_by_precedence";
    }
    std::vector<unsigned int> unit_positive_frame_indices;
    if (unit_positive_active_index_enabled) {
      unit_positive_frame_indices.reserve(frame_count_);
      for (std::size_t index = 0; index < frame_count_; ++index) {
        const float weight = weights[index];
        if (std::isfinite(weight) && weight > 0.0f) {
          unit_positive_frame_indices.push_back(static_cast<unsigned int>(index));
        }
      }
    }
    std::vector<unsigned char> unit_positive_frame_mask;
    if (unit_positive_weight_mask_enabled) {
      unit_positive_frame_mask.reserve(frame_count_);
      for (std::size_t index = 0; index < frame_count_; ++index) {
        const float weight = weights[index];
        unit_positive_frame_mask.push_back(
            (std::isfinite(weight) && weight > 0.0f) ? static_cast<unsigned char>(1) : static_cast<unsigned char>(0));
      }
    }
    const std::size_t unit_positive_active_frame_count = unit_positive_frame_indices.size();
    const std::string percentile_strategy = radix_select_enabled
        ? "radix_select_order_statistics_scan"
        : "ascending_unique_quartile_quickselect_order_statistics";
    const std::string sample_reuse_strategy = radix_select_enabled
        ? "radix_select_global_rescan_weighted_samples"
        : (unit_positive_active_index_enabled
               ? "active_index_global_reread_unit_positive_weights"
               : (unit_positive_local_reuse_enabled
                      ? "local_ordered_reuse_unit_positive_weights"
                      : (unit_positive_selected_reuse_enabled
                             ? "selected_buffer_reuse_unit_positive_weights"
                             : (unit_positive_weight_mask_enabled
                                    ? "frame_mask_global_reread_unit_positive_weights"
                                    : "global_reread_weighted_samples"))));
    const unsigned long long native_admission_frame_limit =
        radix_select_enabled ? 0ull : static_cast<unsigned long long>(512);
    const unsigned long long native_kernel_frame_capacity =
        radix_select_enabled
            ? static_cast<unsigned long long>(unit_positive_weight_frame_count)
            : static_cast<unsigned long long>(
                  unit_positive_weight_frame_count <= 256 ? 256 : 512);
    const unsigned long long hardened_kernel_threads_per_block = 256ull;
    const std::string native_kernel_capacity_selector = radix_select_enabled
        ? "radix_select_unbounded_positive_samples"
        : (unit_positive_weight_frame_count <= 256 ? "small_256" : "large_512");
    const bool native_weight_buffer_required =
        radix_select_enabled || unit_positive_local_reuse_enabled ||
        (!unit_positive_active_index_enabled && !unit_positive_weight_mask_enabled);
    const unsigned long long native_weight_buffer_uploaded_bytes =
        native_weight_buffer_required
            ? static_cast<unsigned long long>(frame_count_ * sizeof(float))
            : 0ull;

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    py::array_t<float> weight_map;
    py::object weight_obj = py::none();
    float* weight_ptr = nullptr;
    if (download_weight_map) {
      weight_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info weight_map_info = weight_map.request();
      weight_ptr = static_cast<float*>(weight_map_info.ptr);
      weight_obj = weight_map;
    }

    float* d_weights = nullptr;
    unsigned int* d_unit_positive_frame_indices = nullptr;
    unsigned char* d_unit_positive_frame_mask = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    const bool synthesize_unit_weight_map_from_u16_coverage =
        count_map_dtype == "uint16" && download_weight_map && download_diagnostics &&
        unit_positive_weights;
    if (count_map_dtype == "uint16") {
      double allocation_s = 0.0;
      double weights_upload_s = 0.0;
      double kernel_sync_s = 0.0;
      double device_download_s = 0.0;
      double weight_map_host_synthesis_s = 0.0;
      double download_s = 0.0;
      double free_s = 0.0;
      const bool materialize_device_weight_map =
          download_weight_map && !synthesize_unit_weight_map_from_u16_coverage;
      py::array_t<std::uint16_t> coverage_map;
      py::array_t<std::uint16_t> low_rejection_map;
      py::array_t<std::uint16_t> high_rejection_map;
      py::object coverage_obj = py::none();
      py::object low_obj = py::none();
      py::object high_obj = py::none();
      unsigned short* coverage_ptr = nullptr;
      unsigned short* low_ptr = nullptr;
      unsigned short* high_ptr = nullptr;
      if (download_diagnostics) {
        coverage_map = py::array_t<std::uint16_t>(
            {static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
        low_rejection_map = py::array_t<std::uint16_t>(
            {static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
        high_rejection_map = py::array_t<std::uint16_t>(
            {static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
        const py::buffer_info coverage_info = coverage_map.request();
        const py::buffer_info low_info = low_rejection_map.request();
        const py::buffer_info high_info = high_rejection_map.request();
        coverage_ptr = static_cast<unsigned short*>(coverage_info.ptr);
        low_ptr = static_cast<unsigned short*>(low_info.ptr);
        high_ptr = static_cast<unsigned short*>(high_info.ptr);
        coverage_obj = coverage_map;
        low_obj = low_rejection_map;
        high_obj = high_rejection_map;
      }
      unsigned short* d_coverage_map = nullptr;
      unsigned short* d_low_rejection_map = nullptr;
      unsigned short* d_high_rejection_map = nullptr;
      try {
        const auto allocation_start = Clock::now();
        if (native_weight_buffer_required) {
          check_cuda(
              cudaMalloc(&d_weights, frame_count_ * sizeof(float)),
              "cudaMalloc(resident hardened winsor weights)");
        }
        if (unit_positive_active_index_enabled && unit_positive_active_frame_count > 0) {
          check_cuda(
              cudaMalloc(
                  &d_unit_positive_frame_indices,
                  unit_positive_active_frame_count * sizeof(unsigned int)),
              "cudaMalloc(resident hardened winsor unit positive frame indices)");
        }
        if (unit_positive_weight_mask_enabled && !unit_positive_frame_mask.empty()) {
          check_cuda(
              cudaMalloc(
                  &d_unit_positive_frame_mask,
                  unit_positive_frame_mask.size() * sizeof(unsigned char)),
              "cudaMalloc(resident hardened winsor unit positive frame mask)");
        }
        check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident hardened winsor master)");
        if (materialize_device_weight_map) {
          check_cuda(
              cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
              "cudaMalloc(resident hardened winsor weight map)");
        }
        if (download_diagnostics) {
          check_cuda(
              cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(unsigned short)),
              "cudaMalloc(resident hardened winsor uint16 coverage map)");
          check_cuda(
              cudaMalloc(&d_low_rejection_map, pixels_per_frame_ * sizeof(unsigned short)),
              "cudaMalloc(resident hardened winsor uint16 low rejection map)");
          check_cuda(
              cudaMalloc(&d_high_rejection_map, pixels_per_frame_ * sizeof(unsigned short)),
              "cudaMalloc(resident hardened winsor uint16 high rejection map)");
        }
        allocation_s = seconds_since(allocation_start);
        const auto weights_upload_start = Clock::now();
        if (d_weights != nullptr) {
          check_cuda(
              cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
              "cudaMemcpy(resident hardened winsor weights)");
        }
        if (d_unit_positive_frame_indices != nullptr) {
          check_cuda(
              cudaMemcpy(
                  d_unit_positive_frame_indices,
                  unit_positive_frame_indices.data(),
                  unit_positive_active_frame_count * sizeof(unsigned int),
                  cudaMemcpyHostToDevice),
              "cudaMemcpy(resident hardened winsor unit positive frame indices)");
        }
        if (d_unit_positive_frame_mask != nullptr) {
          check_cuda(
              cudaMemcpy(
                  d_unit_positive_frame_mask,
                  unit_positive_frame_mask.data(),
                  unit_positive_frame_mask.size() * sizeof(unsigned char),
                  cudaMemcpyHostToDevice),
              "cudaMemcpy(resident hardened winsor unit positive frame mask)");
        }
        weights_upload_s = seconds_since(weights_upload_start);
        const auto kernel_start = Clock::now();
        if (radix_select_enabled) {
          glass_integrate_resident_hardened_winsorized_sigma_f32_radix_select_u16_counts_launch(
              d_stack_,
              d_weights,
              d_master,
              d_weight_map,
              d_coverage_map,
              d_low_rejection_map,
              d_high_rejection_map,
              frame_count_,
              pixels_per_frame_,
              low_sigma,
              high_sigma,
              min_samples,
              max_reject_fraction);
        } else {
          glass_integrate_resident_hardened_winsorized_sigma_f32_u16_counts_launch(
              d_stack_,
              d_weights,
              d_unit_positive_frame_indices,
              d_unit_positive_frame_mask,
              d_master,
              d_weight_map,
              d_coverage_map,
              d_low_rejection_map,
              d_high_rejection_map,
              frame_count_,
              unit_positive_weight_frame_count,
              pixels_per_frame_,
              low_sigma,
              high_sigma,
              min_samples,
              max_reject_fraction,
              unit_positive_active_index_enabled,
              unit_positive_weight_mask_enabled,
              unit_positive_local_reuse_enabled,
              unit_positive_selected_reuse_enabled);
        }
        check_cuda(
            cudaGetLastError(),
            "ResidentCalibratedStack.integrate_hardened_winsorized_sigma uint16 kernel launch");
        check_cuda(
            cudaDeviceSynchronize(),
            "ResidentCalibratedStack.integrate_hardened_winsorized_sigma uint16 synchronize");
        kernel_sync_s = seconds_since(kernel_start);
        const auto download_start = Clock::now();
        check_cuda(
            cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident hardened winsor master)");
        if (materialize_device_weight_map) {
          check_cuda(
              cudaMemcpy(
                  weight_ptr,
                  d_weight_map,
                  pixels_per_frame_ * sizeof(float),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident hardened winsor weight map)");
        }
        if (download_diagnostics) {
          check_cuda(
              cudaMemcpy(
                  coverage_ptr,
                  d_coverage_map,
                  pixels_per_frame_ * sizeof(unsigned short),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident hardened winsor uint16 coverage map)");
          check_cuda(
              cudaMemcpy(
                  low_ptr,
                  d_low_rejection_map,
                  pixels_per_frame_ * sizeof(unsigned short),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident hardened winsor uint16 low rejection map)");
          check_cuda(
              cudaMemcpy(
                  high_ptr,
                  d_high_rejection_map,
                  pixels_per_frame_ * sizeof(unsigned short),
                  cudaMemcpyDeviceToHost),
              "cudaMemcpy(resident hardened winsor uint16 high rejection map)");
        }
        device_download_s = seconds_since(download_start);
        if (synthesize_unit_weight_map_from_u16_coverage) {
          const auto synthesis_start = Clock::now();
          for (std::size_t pixel_index = 0; pixel_index < pixels_per_frame_; ++pixel_index) {
            weight_ptr[pixel_index] = static_cast<float>(coverage_ptr[pixel_index]);
          }
          weight_map_host_synthesis_s = seconds_since(synthesis_start);
        }
        download_s = seconds_since(download_start);
      } catch (...) {
        cudaFree(d_weights);
        cudaFree(d_unit_positive_frame_indices);
        cudaFree(d_unit_positive_frame_mask);
        cudaFree(d_master);
        cudaFree(d_weight_map);
        cudaFree(d_coverage_map);
        cudaFree(d_low_rejection_map);
        cudaFree(d_high_rejection_map);
        throw;
      }
      const auto free_start = Clock::now();
      cudaFree(d_weights);
      cudaFree(d_unit_positive_frame_indices);
      cudaFree(d_unit_positive_frame_mask);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_low_rejection_map);
      cudaFree(d_high_rejection_map);
      free_s = seconds_since(free_start);
      if (profile) {
        py::dict profile_info;
        profile_info["schema_version"] = 1;
        profile_info["native_profile_model"] = "chrono_allocation_upload_kernel_download_free";
        profile_info["percentile_strategy"] = percentile_strategy;
        profile_info["fallback_scale_strategy"] = "lazy_iqr_degenerate_frame_axis_rescan";
        profile_info["fallback_scale_default_path"] = "median_iqr_scale_without_fallback_std";
        profile_info["winsorized_accumulation_order"] = "frame_axis_input_order";
        profile_info["rejection_guard_early_disallow_enabled"] = true;
        profile_info["rejection_guard_early_disallow_model"] =
            "break_reject_count_when_fraction_or_min_samples_already_fails";
        profile_info["sample_reuse_strategy"] = sample_reuse_strategy;
        profile_info["native_frame_count_exceeds_limit"] = frame_count_ > 512;
        profile_info["native_active_count_admission_enabled"] =
            frame_count_ > 512 && unit_positive_weight_frame_count <= 512;
        profile_info["native_admission_sample_count"] =
            static_cast<unsigned long long>(unit_positive_weight_frame_count);
        profile_info["native_admission_frame_limit"] = native_admission_frame_limit;
        profile_info["native_kernel_frame_capacity"] = native_kernel_frame_capacity;
        profile_info["native_kernel_capacity_selector"] = native_kernel_capacity_selector;
        profile_info["hardened_kernel_threads_per_block"] = hardened_kernel_threads_per_block;
        profile_info["radix_select_requested"] = radix_select_requested;
        profile_info["radix_select_enabled"] = radix_select_enabled;
        profile_info["radix_select_positive_sample_count"] =
            static_cast<unsigned long long>(unit_positive_weight_frame_count);
        profile_info["unit_positive_weights_detected"] = unit_positive_weights;
        profile_info["unit_positive_weights_fast_path"] = unit_positive_active_index_enabled;
        profile_info["unit_positive_local_reuse_requested"] = unit_positive_local_reuse_requested;
        profile_info["unit_positive_local_reuse_enabled"] = unit_positive_local_reuse_enabled;
        profile_info["unit_positive_selected_reuse_requested"] =
            unit_positive_selected_reuse_requested;
        profile_info["unit_positive_selected_reuse_enabled"] =
            unit_positive_selected_reuse_enabled;
        profile_info["unit_positive_selected_reuse_reason"] =
            unit_positive_selected_reuse_reason;
        profile_info["unit_positive_active_index_requested"] = unit_positive_active_index_requested;
        profile_info["unit_positive_active_index_reason"] = unit_positive_active_index_enabled
            ? (unit_positive_active_count_admission ? "native_active_count_admission_over_frame_limit"
                                                    : "environment_enabled")
            : "disabled";
        profile_info["unit_positive_weight_mask_requested"] = unit_positive_weight_mask_requested;
        profile_info["unit_positive_weight_mask_enabled"] = unit_positive_weight_mask_enabled;
        profile_info["unit_positive_weight_mask_reason"] = unit_positive_weight_mask_reason;
        profile_info["unit_positive_weight_mask_policy_source"] =
            unit_positive_weight_mask_policy_source;
        profile_info["unit_positive_weight_mask_default_enabled"] =
            unit_positive_weight_mask_default_enabled;
        profile_info["unit_positive_weight_frame_count"] =
            static_cast<unsigned long long>(unit_positive_weight_frame_count);
        profile_info["unit_positive_active_frame_count"] =
            static_cast<unsigned long long>(unit_positive_active_frame_count);
        profile_info["unit_positive_active_index_env_enabled"] = unit_positive_active_index_enabled;
        profile_info["unit_positive_weight_mask_bytes"] =
            static_cast<unsigned long long>(unit_positive_frame_mask.size());
        profile_info["native_weight_buffer_required"] = native_weight_buffer_required;
        profile_info["native_weight_buffer_device_materialized"] = d_weights != nullptr;
        profile_info["native_weight_buffer_upload_skipped"] = !native_weight_buffer_required;
        profile_info["native_weight_buffer_uploaded_bytes"] = native_weight_buffer_uploaded_bytes;
        profile_info["allocation_s"] = allocation_s;
        profile_info["weights_upload_s"] = weights_upload_s;
        profile_info["kernel_sync_s"] = kernel_sync_s;
        profile_info["device_download_s"] = device_download_s;
        profile_info["weight_map_host_synthesis_s"] = weight_map_host_synthesis_s;
        profile_info["download_s"] = download_s;
        profile_info["free_s"] = free_s;
        profile_info["count_map_dtype"] = count_map_dtype;
        profile_info["download_mode"] = download_mode;
        profile_info["diagnostic_maps_downloaded"] = download_diagnostics;
        profile_info["weight_map_downloaded"] = download_weight_map;
        profile_info["unit_positive_weight_map_from_coverage"] =
            synthesize_unit_weight_map_from_u16_coverage;
        profile_info["weight_map_device_materialized"] = materialize_device_weight_map;
        profile_info["weight_map_download_source"] =
            synthesize_unit_weight_map_from_u16_coverage
                ? "coverage_map_uint16_host_expand"
                : (download_weight_map ? "device_weight_map" : "not_requested");
        profile_info["returned_arrays"] =
            1 + (download_weight_map ? 1 : 0) + (download_diagnostics ? 3 : 0);
        profile_info["device_downloaded_arrays"] =
            1 + (materialize_device_weight_map ? 1 : 0) + (download_diagnostics ? 3 : 0);
        profile_info["downloaded_arrays"] =
            1 + (materialize_device_weight_map ? 1 : 0) + (download_diagnostics ? 3 : 0);
        profile_info["downloaded_bytes"] = static_cast<unsigned long long>(
            pixels_per_frame_ *
            (sizeof(float) + (materialize_device_weight_map ? sizeof(float) : 0) +
             (download_diagnostics ? 3 * sizeof(unsigned short) : 0)));
        profile_info["host_synthesized_bytes"] = static_cast<unsigned long long>(
            synthesize_unit_weight_map_from_u16_coverage
                ? pixels_per_frame_ * sizeof(float)
                : 0);
        return py::make_tuple(master, weight_obj, coverage_obj, low_obj, high_obj, profile_info);
      }
      return py::make_tuple(master, weight_obj, coverage_obj, low_obj, high_obj);
    }

    double allocation_s = 0.0;
    double weights_upload_s = 0.0;
    double kernel_sync_s = 0.0;
    double download_s = 0.0;
    double free_s = 0.0;
    py::array_t<float> coverage_map;
    py::array_t<float> low_rejection_map;
    py::array_t<float> high_rejection_map;
    py::object coverage_obj = py::none();
    py::object low_obj = py::none();
    py::object high_obj = py::none();
    float* coverage_ptr = nullptr;
    float* low_ptr = nullptr;
    float* high_ptr = nullptr;
    if (download_diagnostics) {
      coverage_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      low_rejection_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      high_rejection_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info coverage_info = coverage_map.request();
      const py::buffer_info low_info = low_rejection_map.request();
      const py::buffer_info high_info = high_rejection_map.request();
      coverage_ptr = static_cast<float*>(coverage_info.ptr);
      low_ptr = static_cast<float*>(low_info.ptr);
      high_ptr = static_cast<float*>(high_info.ptr);
      coverage_obj = coverage_map;
      low_obj = low_rejection_map;
      high_obj = high_rejection_map;
    }
    float* d_coverage_map = nullptr;
    float* d_low_rejection_map = nullptr;
    float* d_high_rejection_map = nullptr;
    try {
      const auto allocation_start = Clock::now();
      if (native_weight_buffer_required) {
        check_cuda(
            cudaMalloc(&d_weights, frame_count_ * sizeof(float)),
            "cudaMalloc(resident hardened winsor weights)");
      }
      if (unit_positive_active_index_enabled && unit_positive_active_frame_count > 0) {
        check_cuda(
            cudaMalloc(
                &d_unit_positive_frame_indices,
                unit_positive_active_frame_count * sizeof(unsigned int)),
            "cudaMalloc(resident hardened winsor unit positive frame indices)");
      }
      if (unit_positive_weight_mask_enabled && !unit_positive_frame_mask.empty()) {
        check_cuda(
            cudaMalloc(
                &d_unit_positive_frame_mask,
                unit_positive_frame_mask.size() * sizeof(unsigned char)),
            "cudaMalloc(resident hardened winsor unit positive frame mask)");
      }
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident hardened winsor master)");
      if (download_weight_map) {
        check_cuda(
            cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident hardened winsor weight map)");
      }
      if (download_diagnostics) {
        check_cuda(
            cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident hardened winsor coverage map)");
        check_cuda(
            cudaMalloc(&d_low_rejection_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident hardened winsor low rejection map)");
        check_cuda(
            cudaMalloc(&d_high_rejection_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(resident hardened winsor high rejection map)");
      }
      allocation_s = seconds_since(allocation_start);
      const auto weights_upload_start = Clock::now();
      if (d_weights != nullptr) {
        check_cuda(
            cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
            "cudaMemcpy(resident hardened winsor weights)");
      }
      if (d_unit_positive_frame_indices != nullptr) {
        check_cuda(
            cudaMemcpy(
                d_unit_positive_frame_indices,
                unit_positive_frame_indices.data(),
                unit_positive_active_frame_count * sizeof(unsigned int),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident hardened winsor unit positive frame indices)");
      }
      if (d_unit_positive_frame_mask != nullptr) {
        check_cuda(
            cudaMemcpy(
                d_unit_positive_frame_mask,
                unit_positive_frame_mask.data(),
                unit_positive_frame_mask.size() * sizeof(unsigned char),
                cudaMemcpyHostToDevice),
            "cudaMemcpy(resident hardened winsor unit positive frame mask)");
      }
      weights_upload_s = seconds_since(weights_upload_start);
      const auto kernel_start = Clock::now();
      if (radix_select_enabled) {
        glass_integrate_resident_hardened_winsorized_sigma_f32_radix_select_launch(
            d_stack_,
            d_weights,
            d_master,
            d_weight_map,
            d_coverage_map,
            d_low_rejection_map,
            d_high_rejection_map,
            frame_count_,
            pixels_per_frame_,
            low_sigma,
            high_sigma,
            min_samples,
            max_reject_fraction);
      } else {
        glass_integrate_resident_hardened_winsorized_sigma_f32_launch(
            d_stack_,
            d_weights,
            d_unit_positive_frame_indices,
            d_unit_positive_frame_mask,
            d_master,
            d_weight_map,
            d_coverage_map,
            d_low_rejection_map,
            d_high_rejection_map,
            frame_count_,
            unit_positive_weight_frame_count,
            pixels_per_frame_,
            low_sigma,
            high_sigma,
            min_samples,
            max_reject_fraction,
            unit_positive_active_index_enabled,
            unit_positive_weight_mask_enabled,
            unit_positive_local_reuse_enabled,
            unit_positive_selected_reuse_enabled);
      }
      check_cuda(
          cudaGetLastError(),
          "ResidentCalibratedStack.integrate_hardened_winsorized_sigma kernel launch");
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.integrate_hardened_winsorized_sigma synchronize");
      kernel_sync_s = seconds_since(kernel_start);
      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident hardened winsor master)");
      if (download_weight_map) {
        check_cuda(
            cudaMemcpy(
                weight_ptr,
                d_weight_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident hardened winsor weight map)");
      }
      if (download_diagnostics) {
        check_cuda(
            cudaMemcpy(
                coverage_ptr,
                d_coverage_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident hardened winsor coverage map)");
        check_cuda(
            cudaMemcpy(
                low_ptr,
                d_low_rejection_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident hardened winsor low rejection map)");
        check_cuda(
            cudaMemcpy(
                high_ptr,
                d_high_rejection_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(resident hardened winsor high rejection map)");
      }
      download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_unit_positive_frame_indices);
      cudaFree(d_unit_positive_frame_mask);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_low_rejection_map);
      cudaFree(d_high_rejection_map);
      throw;
    }
    const auto free_start = Clock::now();
    cudaFree(d_weights);
    cudaFree(d_unit_positive_frame_indices);
    cudaFree(d_unit_positive_frame_mask);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_low_rejection_map);
    cudaFree(d_high_rejection_map);
    free_s = seconds_since(free_start);
    if (profile) {
      py::dict profile_info;
      profile_info["schema_version"] = 1;
      profile_info["native_profile_model"] = "chrono_allocation_upload_kernel_download_free";
      profile_info["percentile_strategy"] = percentile_strategy;
      profile_info["fallback_scale_strategy"] = "lazy_iqr_degenerate_frame_axis_rescan";
      profile_info["fallback_scale_default_path"] = "median_iqr_scale_without_fallback_std";
      profile_info["winsorized_accumulation_order"] = "frame_axis_input_order";
      profile_info["rejection_guard_early_disallow_enabled"] = true;
      profile_info["rejection_guard_early_disallow_model"] =
          "break_reject_count_when_fraction_or_min_samples_already_fails";
      profile_info["sample_reuse_strategy"] = sample_reuse_strategy;
      profile_info["native_frame_count_exceeds_limit"] = frame_count_ > 512;
      profile_info["native_active_count_admission_enabled"] =
          frame_count_ > 512 && unit_positive_weight_frame_count <= 512;
      profile_info["native_admission_sample_count"] =
          static_cast<unsigned long long>(unit_positive_weight_frame_count);
      profile_info["native_admission_frame_limit"] = native_admission_frame_limit;
      profile_info["native_kernel_frame_capacity"] = native_kernel_frame_capacity;
      profile_info["native_kernel_capacity_selector"] = native_kernel_capacity_selector;
      profile_info["hardened_kernel_threads_per_block"] = hardened_kernel_threads_per_block;
      profile_info["radix_select_requested"] = radix_select_requested;
      profile_info["radix_select_enabled"] = radix_select_enabled;
      profile_info["radix_select_positive_sample_count"] =
          static_cast<unsigned long long>(unit_positive_weight_frame_count);
      profile_info["unit_positive_weights_detected"] = unit_positive_weights;
      profile_info["unit_positive_weights_fast_path"] = unit_positive_active_index_enabled;
      profile_info["unit_positive_local_reuse_requested"] = unit_positive_local_reuse_requested;
      profile_info["unit_positive_local_reuse_enabled"] = unit_positive_local_reuse_enabled;
      profile_info["unit_positive_selected_reuse_requested"] =
          unit_positive_selected_reuse_requested;
      profile_info["unit_positive_selected_reuse_enabled"] =
          unit_positive_selected_reuse_enabled;
      profile_info["unit_positive_selected_reuse_reason"] =
          unit_positive_selected_reuse_reason;
      profile_info["unit_positive_active_index_requested"] = unit_positive_active_index_requested;
      profile_info["unit_positive_active_index_reason"] = unit_positive_active_index_enabled
          ? (unit_positive_active_count_admission ? "native_active_count_admission_over_frame_limit"
                                                  : "environment_enabled")
          : "disabled";
      profile_info["unit_positive_weight_mask_requested"] = unit_positive_weight_mask_requested;
      profile_info["unit_positive_weight_mask_enabled"] = unit_positive_weight_mask_enabled;
      profile_info["unit_positive_weight_mask_reason"] = unit_positive_weight_mask_reason;
      profile_info["unit_positive_weight_mask_policy_source"] =
          unit_positive_weight_mask_policy_source;
      profile_info["unit_positive_weight_mask_default_enabled"] =
          unit_positive_weight_mask_default_enabled;
      profile_info["unit_positive_weight_frame_count"] =
          static_cast<unsigned long long>(unit_positive_weight_frame_count);
      profile_info["unit_positive_active_frame_count"] =
          static_cast<unsigned long long>(unit_positive_active_frame_count);
      profile_info["unit_positive_active_index_env_enabled"] = unit_positive_active_index_enabled;
      profile_info["unit_positive_weight_mask_bytes"] =
          static_cast<unsigned long long>(unit_positive_frame_mask.size());
      profile_info["native_weight_buffer_required"] = native_weight_buffer_required;
      profile_info["native_weight_buffer_device_materialized"] = d_weights != nullptr;
      profile_info["native_weight_buffer_upload_skipped"] = !native_weight_buffer_required;
      profile_info["native_weight_buffer_uploaded_bytes"] = native_weight_buffer_uploaded_bytes;
      profile_info["allocation_s"] = allocation_s;
      profile_info["weights_upload_s"] = weights_upload_s;
      profile_info["kernel_sync_s"] = kernel_sync_s;
      profile_info["download_s"] = download_s;
      profile_info["free_s"] = free_s;
      profile_info["count_map_dtype"] = count_map_dtype;
      profile_info["download_mode"] = download_mode;
      profile_info["diagnostic_maps_downloaded"] = download_diagnostics;
      profile_info["weight_map_downloaded"] = download_weight_map;
      profile_info["downloaded_arrays"] =
          1 + (download_weight_map ? 1 : 0) + (download_diagnostics ? 3 : 0);
      profile_info["downloaded_bytes"] = static_cast<unsigned long long>(
          pixels_per_frame_ *
          (sizeof(float) + (download_weight_map ? sizeof(float) : 0) +
           (download_diagnostics ? 3 * sizeof(float) : 0)));
      return py::make_tuple(master, weight_obj, coverage_obj, low_obj, high_obj, profile_info);
    }
    return py::make_tuple(master, weight_obj, coverage_obj, low_obj, high_obj);
  }

  py::tuple integrate_tile_local_sigma_clip(
      py::object target_mask_obj,
      py::object tile_extents_obj,
      py::object tile_multipliers_obj,
      py::object weights_obj,
      float low_sigma,
      float high_sigma,
      bool winsorize) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before integration");
    }
    if (low_sigma <= 0.0f || high_sigma <= 0.0f) {
      throw std::invalid_argument("sigma thresholds must be positive");
    }
    if (width_ > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        height_ > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("resident tile-local integration requires image dimensions within int range");
    }

    const auto total_start = Clock::now();
    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    auto target_mask_array =
        py::cast<py::array_t<unsigned char, py::array::c_style | py::array::forcecast>>(target_mask_obj);
    const py::buffer_info target_mask_info = target_mask_array.request();
    if (target_mask_info.ndim != 1 ||
        static_cast<std::size_t>(target_mask_info.shape[0]) != frame_count_) {
      throw std::invalid_argument("target_mask must have shape (frame_count,)");
    }
    const auto* target_mask_ptr = static_cast<const unsigned char*>(target_mask_info.ptr);
    std::vector<unsigned char> target_mask(target_mask_ptr, target_mask_ptr + frame_count_);
    std::size_t target_frame_count = 0;
    for (const unsigned char value : target_mask) {
      if (value != 0) {
        ++target_frame_count;
      }
    }
    if (target_frame_count == 0) {
      throw std::invalid_argument("target_mask must select at least one resident frame");
    }

    auto tile_extents_array =
        py::cast<py::array_t<int, py::array::c_style | py::array::forcecast>>(tile_extents_obj);
    const py::buffer_info tile_extents_info = tile_extents_array.request();
    if (tile_extents_info.ndim != 2 || tile_extents_info.shape[1] != 4) {
      throw std::invalid_argument("tile_extents must have shape (tile_count, 4)");
    }
    const std::size_t tile_count = static_cast<std::size_t>(tile_extents_info.shape[0]);
    if (tile_count == 0 || tile_count > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
      throw std::invalid_argument("tile_extents must contain between 1 and INT_MAX tiles");
    }
    const auto* tile_extents_ptr = static_cast<const int*>(tile_extents_info.ptr);
    std::vector<int> tile_extents(tile_extents_ptr, tile_extents_ptr + tile_count * 4);

    auto tile_multipliers_array =
        py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(tile_multipliers_obj);
    const py::buffer_info tile_multipliers_info = tile_multipliers_array.request();
    if (tile_multipliers_info.ndim != 1 ||
        static_cast<std::size_t>(tile_multipliers_info.shape[0]) != tile_count) {
      throw std::invalid_argument("tile_multipliers must have shape (tile_count,)");
    }
    const auto* tile_multipliers_ptr = static_cast<const float*>(tile_multipliers_info.ptr);
    std::vector<float> tile_multipliers(tile_multipliers_ptr, tile_multipliers_ptr + tile_count);

    for (std::size_t tile = 0; tile < tile_count; ++tile) {
      const int base = static_cast<int>(tile * 4);
      const int x0 = tile_extents[base + 0];
      const int y0 = tile_extents[base + 1];
      const int x1 = tile_extents[base + 2];
      const int y1 = tile_extents[base + 3];
      if (x0 < 0 || y0 < 0 || x1 <= x0 || y1 <= y0 ||
          x1 > static_cast<int>(width_) || y1 > static_cast<int>(height_)) {
        throw std::invalid_argument("tile_extents must be positive half-open rectangles inside the image");
      }
      const float multiplier = tile_multipliers[tile];
      if (!std::isfinite(multiplier) || multiplier < 0.0f) {
        throw std::invalid_argument("tile_multipliers must be finite non-negative values");
      }
    }
    for (std::size_t left = 0; left < tile_count; ++left) {
      const int left_base = static_cast<int>(left * 4);
      const int left_x0 = tile_extents[left_base + 0];
      const int left_y0 = tile_extents[left_base + 1];
      const int left_x1 = tile_extents[left_base + 2];
      const int left_y1 = tile_extents[left_base + 3];
      for (std::size_t right = left + 1; right < tile_count; ++right) {
        const int right_base = static_cast<int>(right * 4);
        const int right_x0 = tile_extents[right_base + 0];
        const int right_y0 = tile_extents[right_base + 1];
        const int right_x1 = tile_extents[right_base + 2];
        const int right_y1 = tile_extents[right_base + 3];
        if (std::max(left_x0, right_x0) < std::min(left_x1, right_x1) &&
            std::max(left_y0, right_y0) < std::min(left_y1, right_y1)) {
          throw std::invalid_argument("tile_extents must not overlap for deterministic tile-local integration");
        }
      }
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> coverage_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> low_rejection_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> high_rejection_map({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    const py::buffer_info master_info = master.request();
    const py::buffer_info weight_map_info = weight_map.request();
    const py::buffer_info coverage_info = coverage_map.request();
    const py::buffer_info low_info = low_rejection_map.request();
    const py::buffer_info high_info = high_rejection_map.request();

    float* d_weights = nullptr;
    unsigned char* d_target_mask = nullptr;
    int* d_tile_extents = nullptr;
    float* d_tile_multipliers = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    float* d_coverage_map = nullptr;
    float* d_low_rejection_map = nullptr;
    float* d_high_rejection_map = nullptr;
    double device_alloc_s = 0.0;
    double weights_upload_s = 0.0;
    double policy_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(resident tile-local sigma weights)");
      check_cuda(
          cudaMalloc(&d_target_mask, frame_count_ * sizeof(unsigned char)),
          "cudaMalloc(resident tile-local sigma target mask)");
      check_cuda(
          cudaMalloc(&d_tile_extents, tile_count * 4 * sizeof(int)),
          "cudaMalloc(resident tile-local sigma extents)");
      check_cuda(
          cudaMalloc(&d_tile_multipliers, tile_count * sizeof(float)),
          "cudaMalloc(resident tile-local sigma multipliers)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(resident tile-local sigma master)");
      check_cuda(
          cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident tile-local sigma weight map)");
      check_cuda(
          cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident tile-local sigma coverage map)");
      check_cuda(
          cudaMalloc(&d_low_rejection_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident tile-local sigma low rejection map)");
      check_cuda(
          cudaMalloc(&d_high_rejection_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(resident tile-local sigma high rejection map)");
      device_alloc_s = seconds_since(alloc_start);

      const auto weights_upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local sigma weights)");
      weights_upload_s = seconds_since(weights_upload_start);

      const auto policy_upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_target_mask, target_mask.data(), frame_count_ * sizeof(unsigned char), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local sigma target mask)");
      check_cuda(
          cudaMemcpy(d_tile_extents, tile_extents.data(), tile_count * 4 * sizeof(int), cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local sigma extents)");
      check_cuda(
          cudaMemcpy(
              d_tile_multipliers,
              tile_multipliers.data(),
              tile_count * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(resident tile-local sigma multipliers)");
      policy_upload_s = seconds_since(policy_upload_start);

      const auto kernel_start = Clock::now();
      glass_integrate_resident_tile_local_sigma_clip_f32_launch(
          d_stack_,
          d_weights,
          d_target_mask,
          d_tile_extents,
          d_tile_multipliers,
          d_master,
          d_weight_map,
          d_coverage_map,
          d_low_rejection_map,
          d_high_rejection_map,
          frame_count_,
          static_cast<int>(width_),
          static_cast<int>(height_),
          static_cast<int>(tile_count),
          low_sigma,
          high_sigma,
          winsorize);
      kernel_enqueue_s = seconds_since(kernel_start);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_tile_local_sigma_clip kernel launch");
      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_tile_local_sigma_clip synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local sigma master)");
      check_cuda(
          cudaMemcpy(
              weight_map_info.ptr,
              d_weight_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local sigma weight map)");
      check_cuda(
          cudaMemcpy(
              coverage_info.ptr,
              d_coverage_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local sigma coverage map)");
      check_cuda(
          cudaMemcpy(
              low_info.ptr,
              d_low_rejection_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local sigma low rejection map)");
      check_cuda(
          cudaMemcpy(
              high_info.ptr,
              d_high_rejection_map,
              pixels_per_frame_ * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(resident tile-local sigma high rejection map)");
      download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_target_mask);
      cudaFree(d_tile_extents);
      cudaFree(d_tile_multipliers);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_low_rejection_map);
      cudaFree(d_high_rejection_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_target_mask);
    cudaFree(d_tile_extents);
    cudaFree(d_tile_multipliers);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_low_rejection_map);
    cudaFree(d_high_rejection_map);

    py::dict timing;
    timing["schema_version"] = 1;
    timing["timing_model"] = "native_resident_tile_local_sigma_clip_one_sync";
    timing["rejection"] = winsorize ? "winsorized_sigma" : "sigma_clip";
    timing["frame_count"] = static_cast<unsigned long long>(frame_count_);
    timing["target_frame_count"] = static_cast<unsigned long long>(target_frame_count);
    timing["tile_count"] = static_cast<unsigned long long>(tile_count);
    timing["low_sigma"] = low_sigma;
    timing["high_sigma"] = high_sigma;
    timing["winsorize"] = winsorize;
    timing["device_alloc_s"] = device_alloc_s;
    timing["weights_upload_s"] = weights_upload_s;
    timing["policy_upload_s"] = policy_upload_s;
    timing["kernel_enqueue_s"] = kernel_enqueue_s;
    timing["sync_s"] = sync_s;
    timing["download_s"] = download_s;
    timing["total_s"] = seconds_since(total_start);
    timing["weights_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(float));
    timing["target_mask_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(unsigned char));
    timing["tile_extents_bytes"] = static_cast<unsigned long long>(tile_count * 4 * sizeof(int));
    timing["tile_multipliers_bytes"] = static_cast<unsigned long long>(tile_count * sizeof(float));
    timing["output_bytes"] = static_cast<unsigned long long>(pixels_per_frame_ * sizeof(float) * 5);
    timing["modifies_resident_stack"] = false;
    return py::make_tuple(
        master,
        weight_map,
        coverage_map,
        low_rejection_map,
        high_rejection_map,
        timing);
  }

  py::tuple integrate_matrix_warped_mean(
      py::object matrices_obj,
      py::object weights_obj,
      const std::string& interpolation,
      float clamping_threshold,
      const std::string& download_mode) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before fused matrix-warped integration");
    }
    if (interpolation != "bilinear" && interpolation != "lanczos3") {
      throw std::invalid_argument("interpolation must be bilinear or lanczos3");
    }
    if (download_mode != "full" && download_mode != "master_weight" && download_mode != "master_only") {
      throw std::invalid_argument("download_mode must be full, master_weight, or master_only");
    }
    const bool download_diagnostics = download_mode == "full";
    const bool download_weight_map = download_mode != "master_only";
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (matrices.size() != frame_count_) {
      throw std::invalid_argument("matrices must have shape (frame_count, 3, 3)");
    }

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map;
    const py::buffer_info master_info = master.request();
    py::object weight_obj = py::none();
    py::object coverage_obj = py::none();
    py::object geometric_obj = py::none();
    float* weight_host_ptr = nullptr;
    float* coverage_host_ptr = nullptr;
    float* geometric_host_ptr = nullptr;
    py::array_t<float> coverage_map;
    py::array_t<float> geometric_coverage_map;
    if (download_weight_map) {
      weight_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info weight_map_info = weight_map.request();
      weight_host_ptr = static_cast<float*>(weight_map_info.ptr);
      weight_obj = weight_map;
    }
    if (download_diagnostics) {
      coverage_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      geometric_coverage_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info coverage_info = coverage_map.request();
      const py::buffer_info geometric_info = geometric_coverage_map.request();
      coverage_host_ptr = static_cast<float*>(coverage_info.ptr);
      geometric_host_ptr = static_cast<float*>(geometric_info.ptr);
      coverage_obj = coverage_map;
      geometric_obj = geometric_coverage_map;
    }

    const auto total_start = Clock::now();
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(frame_count_ * 9, 0.0f);
    for (std::size_t frame = 0; frame < frame_count_; ++frame) {
      const auto inverse = invert_matrix3x3(matrices[frame]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(frame * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);

    float* d_weights = nullptr;
    float* d_inverses = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    float* d_coverage_map = nullptr;
    float* d_geometric_coverage_map = nullptr;
    double device_alloc_s = 0.0;
    double weights_upload_s = 0.0;
    double inverse_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(fused matrix weights)");
      check_cuda(cudaMalloc(&d_inverses, inverse_host.size() * sizeof(float)), "cudaMalloc(fused matrix inverses)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix master)");
      check_cuda(cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix weight map)");
      if (download_diagnostics) {
        check_cuda(cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix coverage)");
        check_cuda(
            cudaMalloc(&d_geometric_coverage_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(fused matrix geometric coverage)");
      }
      device_alloc_s = seconds_since(alloc_start);

      const auto weights_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice, 0),
          "cudaMemcpyAsync(fused matrix weights)");
      weights_upload_s = seconds_since(weights_upload_start);

      const auto inverse_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_inverses,
              inverse_host.data(),
              inverse_host.size() * sizeof(float),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(fused matrix inverses)");
      inverse_upload_s = seconds_since(inverse_upload_start);

      const auto kernel_start = Clock::now();
      glass_integrate_matrix_warped_mean_f32_launch(
          d_stack_,
          d_weights,
          d_inverses,
          d_master,
          d_weight_map,
          d_coverage_map,
          d_geometric_coverage_map,
          frame_count_,
          static_cast<int>(width_),
          static_cast<int>(height_),
          interpolation == "lanczos3" ? 1 : 0,
          clamping_threshold);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_matrix_warped_mean kernel launch");
      kernel_enqueue_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.integrate_matrix_warped_mean synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(fused matrix master)");
      if (download_weight_map) {
        check_cuda(
            cudaMemcpy(
                weight_host_ptr,
                d_weight_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix weight map)");
      }
      if (download_diagnostics) {
        check_cuda(
            cudaMemcpy(
                coverage_host_ptr,
                d_coverage_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix coverage map)");
        check_cuda(
            cudaMemcpy(
                geometric_host_ptr,
                d_geometric_coverage_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix geometric coverage map)");
      }
      download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_inverses);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_geometric_coverage_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_inverses);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_geometric_coverage_map);

    py::dict timing;
    timing["schema_version"] = 1;
    timing["timing_model"] = "native_fused_matrix_warp_weighted_mean_one_sync";
    timing["interpolation"] = interpolation;
    timing["clamping_threshold"] = clamping_threshold;
    timing["rejection"] = "none";
    timing["frame_count"] = static_cast<unsigned long long>(frame_count_);
    timing["inverse_prepare_s"] = inverse_prepare_s;
    timing["device_alloc_s"] = device_alloc_s;
    timing["weights_upload_s"] = weights_upload_s;
    timing["inverse_upload_s"] = inverse_upload_s;
    timing["kernel_enqueue_s"] = kernel_enqueue_s;
    timing["sync_s"] = sync_s;
    timing["download_s"] = download_s;
    timing["total_s"] = seconds_since(total_start);
    timing["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    timing["weights_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(float));
    timing["download_mode"] = download_mode;
    timing["diagnostic_maps_downloaded"] = download_diagnostics;
    timing["weight_map_downloaded"] = download_weight_map;
    timing["output_bytes"] = static_cast<unsigned long long>(
        pixels_per_frame_ * sizeof(float) * (1 + (download_weight_map ? 1 : 0) + (download_diagnostics ? 2 : 0)));
    timing["avoids_stack_scatter"] = true;
    timing["modifies_resident_stack"] = false;
    return py::make_tuple(master, weight_obj, coverage_obj, geometric_obj, timing);
  }

  py::tuple integrate_matrix_warped_sigma_clip(
      py::object matrices_obj,
      py::object weights_obj,
      const std::string& interpolation,
      float clamping_threshold,
      float low_sigma,
      float high_sigma,
      bool winsorize,
      const std::string& download_mode) const {
    if (loaded_count_ != frame_count_) {
      throw std::runtime_error("all resident frames must be loaded before fused matrix-warped sigma integration");
    }
    if (interpolation != "bilinear" && interpolation != "lanczos3") {
      throw std::invalid_argument("interpolation must be bilinear or lanczos3");
    }
    if (low_sigma <= 0.0f || high_sigma <= 0.0f) {
      throw std::invalid_argument("sigma thresholds must be positive");
    }
    if (download_mode != "full" && download_mode != "master_weight" && download_mode != "master_only") {
      throw std::invalid_argument("download_mode must be full, master_weight, or master_only");
    }
    const bool download_diagnostics = download_mode == "full";
    const bool download_weight_map = download_mode != "master_only";
    const auto matrices = parse_matrix_stack(matrices_obj);
    if (matrices.size() != frame_count_) {
      throw std::invalid_argument("matrices must have shape (frame_count, 3, 3)");
    }

    std::vector<float> weights(frame_count_, 1.0f);
    py::array_t<float, py::array::c_style | py::array::forcecast> weights_array;
    if (!weights_obj.is_none()) {
      weights_array = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(weights_obj);
      const py::buffer_info weights_info = weights_array.request();
      if (weights_info.ndim != 1 || static_cast<std::size_t>(weights_info.shape[0]) != frame_count_) {
        throw std::invalid_argument("weights must have shape (frame_count,)");
      }
      const auto* ptr = static_cast<const float*>(weights_info.ptr);
      weights.assign(ptr, ptr + frame_count_);
    }

    py::array_t<float> master({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
    py::array_t<float> weight_map;
    const py::buffer_info master_info = master.request();
    py::object weight_obj = py::none();
    py::object coverage_obj = py::none();
    py::object low_obj = py::none();
    py::object high_obj = py::none();
    py::object geometric_obj = py::none();
    float* weight_host_ptr = nullptr;
    float* coverage_host_ptr = nullptr;
    float* low_host_ptr = nullptr;
    float* high_host_ptr = nullptr;
    float* geometric_host_ptr = nullptr;
    py::array_t<float> coverage_map;
    py::array_t<float> low_rejection_map;
    py::array_t<float> high_rejection_map;
    py::array_t<float> geometric_coverage_map;
    if (download_weight_map) {
      weight_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info weight_map_info = weight_map.request();
      weight_host_ptr = static_cast<float*>(weight_map_info.ptr);
      weight_obj = weight_map;
    }
    if (download_diagnostics) {
      coverage_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      low_rejection_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      high_rejection_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      geometric_coverage_map = py::array_t<float>({static_cast<py::ssize_t>(height_), static_cast<py::ssize_t>(width_)});
      const py::buffer_info coverage_info = coverage_map.request();
      const py::buffer_info low_info = low_rejection_map.request();
      const py::buffer_info high_info = high_rejection_map.request();
      const py::buffer_info geometric_info = geometric_coverage_map.request();
      coverage_host_ptr = static_cast<float*>(coverage_info.ptr);
      low_host_ptr = static_cast<float*>(low_info.ptr);
      high_host_ptr = static_cast<float*>(high_info.ptr);
      geometric_host_ptr = static_cast<float*>(geometric_info.ptr);
      coverage_obj = coverage_map;
      low_obj = low_rejection_map;
      high_obj = high_rejection_map;
      geometric_obj = geometric_coverage_map;
    }

    const auto total_start = Clock::now();
    const auto inverse_prepare_start = Clock::now();
    std::vector<float> inverse_host(frame_count_ * 9, 0.0f);
    for (std::size_t frame = 0; frame < frame_count_; ++frame) {
      const auto inverse = invert_matrix3x3(matrices[frame]);
      std::copy(inverse.begin(), inverse.end(), inverse_host.begin() + static_cast<std::ptrdiff_t>(frame * 9));
    }
    const double inverse_prepare_s = seconds_since(inverse_prepare_start);

    float* d_weights = nullptr;
    float* d_inverses = nullptr;
    float* d_master = nullptr;
    float* d_weight_map = nullptr;
    float* d_coverage_map = nullptr;
    float* d_low_rejection_map = nullptr;
    float* d_high_rejection_map = nullptr;
    float* d_geometric_coverage_map = nullptr;
    double device_alloc_s = 0.0;
    double weights_upload_s = 0.0;
    double inverse_upload_s = 0.0;
    double kernel_enqueue_s = 0.0;
    double sync_s = 0.0;
    double download_s = 0.0;
    try {
      const auto alloc_start = Clock::now();
      check_cuda(cudaMalloc(&d_weights, frame_count_ * sizeof(float)), "cudaMalloc(fused matrix sigma weights)");
      check_cuda(
          cudaMalloc(&d_inverses, inverse_host.size() * sizeof(float)),
          "cudaMalloc(fused matrix sigma inverses)");
      check_cuda(cudaMalloc(&d_master, pixels_per_frame_ * sizeof(float)), "cudaMalloc(fused matrix sigma master)");
      check_cuda(
          cudaMalloc(&d_weight_map, pixels_per_frame_ * sizeof(float)),
          "cudaMalloc(fused matrix sigma weight map)");
      if (download_diagnostics) {
        check_cuda(
            cudaMalloc(&d_coverage_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(fused matrix sigma coverage)");
        check_cuda(
            cudaMalloc(&d_low_rejection_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(fused matrix sigma low rejection)");
        check_cuda(
            cudaMalloc(&d_high_rejection_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(fused matrix sigma high rejection)");
        check_cuda(
            cudaMalloc(&d_geometric_coverage_map, pixels_per_frame_ * sizeof(float)),
            "cudaMalloc(fused matrix sigma geometric coverage)");
      }
      device_alloc_s = seconds_since(alloc_start);

      const auto weights_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(d_weights, weights.data(), frame_count_ * sizeof(float), cudaMemcpyHostToDevice, 0),
          "cudaMemcpyAsync(fused matrix sigma weights)");
      weights_upload_s = seconds_since(weights_upload_start);

      const auto inverse_upload_start = Clock::now();
      check_cuda(
          cudaMemcpyAsync(
              d_inverses,
              inverse_host.data(),
              inverse_host.size() * sizeof(float),
              cudaMemcpyHostToDevice,
              0),
          "cudaMemcpyAsync(fused matrix sigma inverses)");
      inverse_upload_s = seconds_since(inverse_upload_start);

      const auto kernel_start = Clock::now();
      glass_integrate_matrix_warped_sigma_clip_f32_launch(
          d_stack_,
          d_weights,
          d_inverses,
          d_master,
          d_weight_map,
          d_coverage_map,
          d_low_rejection_map,
          d_high_rejection_map,
          d_geometric_coverage_map,
          frame_count_,
          static_cast<int>(width_),
          static_cast<int>(height_),
          interpolation == "lanczos3" ? 1 : 0,
          clamping_threshold,
          low_sigma,
          high_sigma,
          winsorize);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.integrate_matrix_warped_sigma_clip kernel launch");
      kernel_enqueue_s = seconds_since(kernel_start);

      const auto sync_start = Clock::now();
      check_cuda(
          cudaDeviceSynchronize(),
          "ResidentCalibratedStack.integrate_matrix_warped_sigma_clip synchronize");
      sync_s = seconds_since(sync_start);

      const auto download_start = Clock::now();
      check_cuda(
          cudaMemcpy(master_info.ptr, d_master, pixels_per_frame_ * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(fused matrix sigma master)");
      if (download_weight_map) {
        check_cuda(
            cudaMemcpy(
                weight_host_ptr,
                d_weight_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix sigma weight map)");
      }
      if (download_diagnostics) {
        check_cuda(
            cudaMemcpy(
                coverage_host_ptr,
                d_coverage_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix sigma coverage map)");
        check_cuda(
            cudaMemcpy(
                low_host_ptr,
                d_low_rejection_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix sigma low rejection map)");
        check_cuda(
            cudaMemcpy(
                high_host_ptr,
                d_high_rejection_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix sigma high rejection map)");
        check_cuda(
            cudaMemcpy(
                geometric_host_ptr,
                d_geometric_coverage_map,
                pixels_per_frame_ * sizeof(float),
                cudaMemcpyDeviceToHost),
            "cudaMemcpy(fused matrix sigma geometric coverage map)");
      }
      download_s = seconds_since(download_start);
    } catch (...) {
      cudaFree(d_weights);
      cudaFree(d_inverses);
      cudaFree(d_master);
      cudaFree(d_weight_map);
      cudaFree(d_coverage_map);
      cudaFree(d_low_rejection_map);
      cudaFree(d_high_rejection_map);
      cudaFree(d_geometric_coverage_map);
      throw;
    }
    cudaFree(d_weights);
    cudaFree(d_inverses);
    cudaFree(d_master);
    cudaFree(d_weight_map);
    cudaFree(d_coverage_map);
    cudaFree(d_low_rejection_map);
    cudaFree(d_high_rejection_map);
    cudaFree(d_geometric_coverage_map);

    py::dict timing;
    timing["schema_version"] = 1;
    timing["timing_model"] = "native_fused_matrix_warp_sigma_clip_one_sync";
    timing["interpolation"] = interpolation;
    timing["clamping_threshold"] = clamping_threshold;
    timing["rejection"] = winsorize ? "winsorized_sigma" : "sigma_clip";
    timing["winsorize"] = winsorize;
    timing["low_sigma"] = low_sigma;
    timing["high_sigma"] = high_sigma;
    timing["frame_count"] = static_cast<unsigned long long>(frame_count_);
    timing["inverse_prepare_s"] = inverse_prepare_s;
    timing["device_alloc_s"] = device_alloc_s;
    timing["weights_upload_s"] = weights_upload_s;
    timing["inverse_upload_s"] = inverse_upload_s;
    timing["kernel_enqueue_s"] = kernel_enqueue_s;
    timing["sync_s"] = sync_s;
    timing["download_s"] = download_s;
    timing["total_s"] = seconds_since(total_start);
    timing["inverse_batch_bytes"] = static_cast<unsigned long long>(inverse_host.size() * sizeof(float));
    timing["weights_bytes"] = static_cast<unsigned long long>(frame_count_ * sizeof(float));
    timing["download_mode"] = download_mode;
    timing["diagnostic_maps_downloaded"] = download_diagnostics;
    timing["weight_map_downloaded"] = download_weight_map;
    timing["output_bytes"] = static_cast<unsigned long long>(
        pixels_per_frame_ * sizeof(float) * (1 + (download_weight_map ? 1 : 0) + (download_diagnostics ? 4 : 0)));
    timing["avoids_stack_scatter"] = true;
    timing["modifies_resident_stack"] = false;
    return py::make_tuple(
        master,
        weight_obj,
        coverage_obj,
        low_obj,
        high_obj,
        geometric_obj,
        timing);
  }

 private:
  void require_index(std::size_t index) const {
    if (index >= frame_count_) {
      throw std::out_of_range("resident frame index is out of range");
    }
  }

  void require_loaded(std::size_t index, const char* operation) const {
    require_index(index);
    if (!loaded_[index]) {
      throw std::runtime_error(std::string("resident frame must be loaded before ") + operation);
    }
  }

  void mark_loaded(std::size_t index) {
    if (!loaded_[index]) {
      loaded_[index] = 1;
      ++loaded_count_;
    }
  }

  CalibrationParameters calibration_parameters(
      float light_exposure_s,
      py::object dark_exposure_obj,
      py::object policy_obj) const {
    py::dict policy;
    if (!policy_obj.is_none()) {
      policy = py::cast<py::dict>(policy_obj);
    }
    CalibrationParameters params;
    params.master_dark_includes_bias = dict_bool(policy, "master_dark_includes_bias", true);
    params.dark_scaling_enabled = dict_bool(policy, "dark_scaling_enabled", true);
    params.flat_floor = dict_float(policy, "flat_floor", 1.0e-6f);
    params.pedestal = dict_float(policy, "pedestal", 0.0f);
    if (has_dark_ && params.dark_scaling_enabled && !dark_exposure_obj.is_none()) {
      const float dark_exposure_s = py::cast<float>(dark_exposure_obj);
      if (dark_exposure_s != 0.0f) {
        params.dark_scale = light_exposure_s / dark_exposure_s;
      }
    }
    return params;
  }

  py::dict calibration_timing_dict(const ResidentCalibrationTiming& timing, const char* mode) const {
    py::dict out;
    out["schema_version"] = 1;
    out["h2d_mode"] = mode;
    out["event_mode"] = std::string(mode) == "pageable" ? "none" : "reused_stack_events";
    out["host_copy_s"] = timing.host_copy_s;
    out["h2d_s"] = timing.h2d_s;
    out["calibrate_store_s"] = timing.calibrate_store_s;
    out["total_s"] = timing.total_s;
    out["host_pinned_bytes"] = host_pinned_bytes();
    return out;
  }

  void ensure_pinned_light_buffer() {
    if (h_pinned_light_ != nullptr) {
      return;
    }
    check_cuda(
        cudaHostAlloc(
            reinterpret_cast<void**>(&h_pinned_light_),
            pixels_per_frame_ * sizeof(float),
            cudaHostAllocPortable),
        "cudaHostAlloc(resident pinned raw light buffer)");
  }

  void ensure_calibration_lanes(std::size_t lane_count) {
    if (lane_count == 0) {
      return;
    }
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    while (d_calibration_lane_lights_.size() < lane_count) {
      float* buffer = nullptr;
      cudaStream_t stream = nullptr;
      cudaEvent_t start_event = nullptr;
      cudaEvent_t stop_event = nullptr;
      try {
        check_cuda(cudaMalloc(&buffer, frame_bytes), "cudaMalloc(resident multistream raw light lane)");
        check_cuda(cudaStreamCreate(&stream), "cudaStreamCreate(resident multistream calibration lane)");
        check_cuda(cudaEventCreate(&start_event), "cudaEventCreate(resident multistream calibration lane start)");
        check_cuda(cudaEventCreate(&stop_event), "cudaEventCreate(resident multistream calibration lane stop)");
        cudaEvent_t h2d_start_event = nullptr;
        check_cuda(cudaEventCreate(&h2d_start_event), "cudaEventCreate(resident multistream calibration lane h2d start)");
        calibration_lane_h2d_start_events_.push_back(h2d_start_event);
        cudaEvent_t h2d_event = nullptr;
        check_cuda(cudaEventCreate(&h2d_event), "cudaEventCreate(resident multistream calibration lane h2d done)");
        calibration_lane_h2d_events_.push_back(h2d_event);
      } catch (...) {
        if (stop_event != nullptr) {
          cudaEventDestroy(stop_event);
        }
        if (start_event != nullptr) {
          cudaEventDestroy(start_event);
        }
        if (calibration_lane_h2d_start_events_.size() > d_calibration_lane_lights_.size()) {
          cudaEventDestroy(calibration_lane_h2d_start_events_.back());
          calibration_lane_h2d_start_events_.pop_back();
        }
        if (calibration_lane_h2d_events_.size() > d_calibration_lane_lights_.size()) {
          cudaEventDestroy(calibration_lane_h2d_events_.back());
          calibration_lane_h2d_events_.pop_back();
        }
        if (stream != nullptr) {
          cudaStreamDestroy(stream);
        }
        cudaFree(buffer);
        throw;
      }
      d_calibration_lane_lights_.push_back(buffer);
      calibration_lane_streams_.push_back(stream);
      calibration_lane_start_events_.push_back(start_event);
      calibration_lane_stop_events_.push_back(stop_event);
    }
  }

  ResidentCalibrationTiming calibrate_frame_pageable_impl(
      std::size_t index,
      void* light_ptr,
      const CalibrationParameters& params) {
    ResidentCalibrationTiming timing;
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    {
      py::gil_scoped_release release;
      const auto h2d_start = Clock::now();
      check_cuda(
          cudaMemcpy(d_light_, light_ptr, frame_bytes, cudaMemcpyHostToDevice),
          "cudaMemcpy(resident raw light)");
      timing.h2d_s = seconds_since(h2d_start);

      const auto calibrate_start = Clock::now();
      glass_calibrate_tile_f32_launch(
          d_light_,
          d_bias_,
          d_dark_,
          d_flat_,
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          has_bias_,
          has_dark_,
          has_flat_,
          params.master_dark_includes_bias,
          params.dark_scale,
          params.flat_floor,
          params.pedestal);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame kernel launch");
      check_cuda(cudaDeviceSynchronize(), "ResidentCalibratedStack.calibrate_frame synchronize");
      timing.calibrate_store_s = seconds_since(calibrate_start);
    }
    timing.total_s = seconds_since(total_start);
    return timing;
  }

  ResidentCalibrationTiming calibrate_frame_pinned_async_impl(
      std::size_t index,
      void* light_ptr,
      const CalibrationParameters& params) {
    ResidentCalibrationTiming timing;
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    {
      py::gil_scoped_release release;
      ensure_pinned_light_buffer();

      const auto host_copy_start = Clock::now();
      std::memcpy(h_pinned_light_, light_ptr, frame_bytes);
      timing.host_copy_s = seconds_since(host_copy_start);

      check_cuda(cudaEventRecord(calibrate_h2d_start_, calibrate_stream_), "cudaEventRecord(resident pinned h2d start)");
      check_cuda(
          cudaMemcpyAsync(
              d_light_,
              h_pinned_light_,
              frame_bytes,
              cudaMemcpyHostToDevice,
              calibrate_stream_),
          "cudaMemcpyAsync(resident pinned raw light)");
      check_cuda(cudaEventRecord(calibrate_h2d_stop_, calibrate_stream_), "cudaEventRecord(resident pinned h2d stop)");
      check_cuda(
          cudaEventRecord(calibrate_kernel_start_, calibrate_stream_),
          "cudaEventRecord(resident calibration start)");
      glass_calibrate_tile_f32_launch_stream(
          d_light_,
          d_bias_,
          d_dark_,
          d_flat_,
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          has_bias_,
          has_dark_,
          has_flat_,
          params.master_dark_includes_bias,
          params.dark_scale,
          params.flat_floor,
          params.pedestal,
          calibrate_stream_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame_pinned_async kernel launch");
      check_cuda(
          cudaEventRecord(calibrate_kernel_stop_, calibrate_stream_),
          "cudaEventRecord(resident calibration stop)");
      check_cuda(
          cudaStreamSynchronize(calibrate_stream_),
          "ResidentCalibratedStack.calibrate_frame_pinned_async synchronize");
      timing.h2d_s = cuda_event_elapsed_s(
          calibrate_h2d_start_,
          calibrate_h2d_stop_,
          "cudaEventElapsedTime(resident pinned h2d)");
      timing.calibrate_store_s =
          cuda_event_elapsed_s(
              calibrate_kernel_start_,
              calibrate_kernel_stop_,
              "cudaEventElapsedTime(resident calibration)");
    }
    timing.total_s = seconds_since(total_start);
    return timing;
  }

  ResidentCalibrationTiming calibrate_frame_host_async_impl(
      std::size_t index,
      void* light_ptr,
      const CalibrationParameters& params) {
    ResidentCalibrationTiming timing;
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    const auto total_start = Clock::now();
    {
      py::gil_scoped_release release;
      check_cuda(
          cudaEventRecord(calibrate_h2d_start_, calibrate_stream_),
          "cudaEventRecord(resident host async h2d start)");
      check_cuda(
          cudaMemcpyAsync(
              d_light_,
              light_ptr,
              frame_bytes,
              cudaMemcpyHostToDevice,
              calibrate_stream_),
          "cudaMemcpyAsync(resident host raw light)");
      check_cuda(
          cudaEventRecord(calibrate_h2d_stop_, calibrate_stream_),
          "cudaEventRecord(resident host async h2d stop)");
      check_cuda(
          cudaEventRecord(calibrate_kernel_start_, calibrate_stream_),
          "cudaEventRecord(resident host async calibration start)");
      glass_calibrate_tile_f32_launch_stream(
          d_light_,
          d_bias_,
          d_dark_,
          d_flat_,
          d_stack_ + index * pixels_per_frame_,
          pixels_per_frame_,
          has_bias_,
          has_dark_,
          has_flat_,
          params.master_dark_includes_bias,
          params.dark_scale,
          params.flat_floor,
          params.pedestal,
          calibrate_stream_);
      check_cuda(cudaGetLastError(), "ResidentCalibratedStack.calibrate_frame_host_async kernel launch");
      check_cuda(
          cudaEventRecord(calibrate_kernel_stop_, calibrate_stream_),
          "cudaEventRecord(resident host async calibration stop)");
      check_cuda(
          cudaStreamSynchronize(calibrate_stream_),
          "ResidentCalibratedStack.calibrate_frame_host_async synchronize");
      timing.h2d_s = cuda_event_elapsed_s(
          calibrate_h2d_start_,
          calibrate_h2d_stop_,
          "cudaEventElapsedTime(resident host async h2d)");
      timing.calibrate_store_s =
          cuda_event_elapsed_s(
              calibrate_kernel_start_,
              calibrate_kernel_stop_,
              "cudaEventElapsedTime(resident host async calibration)");
    }
    timing.total_s = seconds_since(total_start);
    return timing;
  }

  void upload_optional_master(py::object obj, float** destination, bool* present, const char* name) {
    cudaFree(*destination);
    *destination = nullptr;
    *present = false;
    if (obj.is_none()) {
      return;
    }
    py::array_t<float, py::array::c_style | py::array::forcecast> array =
        py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(obj);
    const py::buffer_info info = array.request();
    require_frame_shape(info, height_, width_);
    check_cuda(cudaMalloc(destination, pixels_per_frame_ * sizeof(float)), name);
    check_cuda(
        cudaMemcpy(*destination, info.ptr, pixels_per_frame_ * sizeof(float), cudaMemcpyHostToDevice),
        name);
    *present = true;
  }

  void allocate_warp_coverage_if_needed() {
    if (d_warp_coverage_ != nullptr) {
      return;
    }
    check_cuda(
        cudaMalloc(&d_warp_coverage_, pixels_per_frame_ * sizeof(float)),
        "cudaMalloc(resident warp coverage accumulator)");
    check_cuda(
        cudaMemset(d_warp_coverage_, 0, pixels_per_frame_ * sizeof(float)),
        "cudaMemset(resident warp coverage accumulator)");
    warp_coverage_frame_count_ = 0;
  }

  struct BatchWarpWorkspace {
    std::unique_ptr<float, CudaFloatFree> output;
    std::unique_ptr<unsigned char, CudaUCharFree> coverage;
    std::unique_ptr<float, CudaFloatFree> inverses;
    std::unique_ptr<unsigned long long, CudaUllFree> indices;
    std::size_t capacity_frames = 0;
    std::size_t output_bytes = 0;
    std::size_t coverage_bytes = 0;
    std::size_t inverse_bytes = 0;
    std::size_t index_bytes = 0;
    double allocation_s = 0.0;
  };

  BatchWarpWorkspace allocate_batch_warp_workspace(
      std::size_t requested_frames,
      std::size_t max_capacity_frames = 0,
      bool include_coverage = true) {
    if (requested_frames == 0) {
      throw std::invalid_argument("batch warp workspace requires at least one frame");
    }
    constexpr std::size_t preferred_frames = 8;
    const std::size_t capacity_limit =
        max_capacity_frames > 0 ? max_capacity_frames : preferred_frames;
    std::size_t capacity = std::min(requested_frames, capacity_limit);
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    cudaError_t last_error = cudaSuccess;
    const auto alloc_start = Clock::now();
    while (capacity > 0) {
      float* raw_output = nullptr;
      unsigned char* raw_coverage = nullptr;
      float* raw_inverses = nullptr;
      unsigned long long* raw_indices = nullptr;
      const std::size_t output_bytes = capacity * frame_bytes;
      const std::size_t coverage_bytes =
          include_coverage ? capacity * pixels_per_frame_ * sizeof(unsigned char) : 0;
      const std::size_t inverse_bytes = requested_frames * 9 * sizeof(float);
      const std::size_t index_bytes = requested_frames * sizeof(unsigned long long);
      last_error = cudaMalloc(&raw_output, output_bytes);
      if (last_error == cudaSuccess && include_coverage) {
        last_error = cudaMalloc(&raw_coverage, coverage_bytes);
      }
      if (last_error == cudaSuccess) {
        last_error = cudaMalloc(&raw_inverses, inverse_bytes);
      }
      if (last_error == cudaSuccess) {
        last_error = cudaMalloc(&raw_indices, index_bytes);
      }
      if (last_error == cudaSuccess) {
        BatchWarpWorkspace workspace;
        workspace.output.reset(raw_output);
        workspace.coverage.reset(raw_coverage);
        workspace.inverses.reset(raw_inverses);
        workspace.indices.reset(raw_indices);
        workspace.capacity_frames = capacity;
        workspace.output_bytes = output_bytes;
        workspace.coverage_bytes = coverage_bytes;
        workspace.inverse_bytes = inverse_bytes;
        workspace.index_bytes = index_bytes;
        workspace.allocation_s = seconds_since(alloc_start);
        return workspace;
      }
      if (raw_output != nullptr) {
        (void)cudaFree(raw_output);
      }
      if (raw_coverage != nullptr) {
        (void)cudaFree(raw_coverage);
      }
      if (raw_inverses != nullptr) {
        (void)cudaFree(raw_inverses);
      }
      if (raw_indices != nullptr) {
        (void)cudaFree(raw_indices);
      }
      (void)cudaGetLastError();
      capacity /= 2;
    }
    std::ostringstream message;
    message << "cudaMalloc(resident batch matrix warp workspace) failed: "
            << cudaGetErrorString(last_error);
    throw std::runtime_error(message.str());
  }

  void allocate_warp_scratch_if_needed(bool matrix_warp) {
    const std::size_t frame_bytes = pixels_per_frame_ * sizeof(float);
    if (d_warp_output_ == nullptr) {
      check_cuda(cudaMalloc(&d_warp_output_, frame_bytes), "cudaMalloc(resident warp scratch output)");
    }
    if (d_warp_frame_coverage_ == nullptr) {
      check_cuda(
          cudaMalloc(&d_warp_frame_coverage_, frame_bytes),
          "cudaMalloc(resident warp scratch coverage)");
    }
    if (matrix_warp && d_warp_inverse_ == nullptr) {
      check_cuda(cudaMalloc(&d_warp_inverse_, 9 * sizeof(float)), "cudaMalloc(resident warp scratch inverse)");
    }
  }

  std::size_t frame_count_;
  std::size_t height_;
  std::size_t width_;
  std::size_t pixels_per_frame_;
  std::size_t loaded_count_ = 0;
  std::size_t warp_coverage_frame_count_ = 0;
  std::vector<unsigned char> loaded_;
  float* d_stack_ = nullptr;
  float* d_light_ = nullptr;
  float* d_bias_ = nullptr;
  float* d_dark_ = nullptr;
  float* d_flat_ = nullptr;
  std::vector<float*> d_calibration_lane_lights_;
  std::vector<cudaStream_t> calibration_lane_streams_;
  std::vector<cudaEvent_t> calibration_lane_start_events_;
  std::vector<cudaEvent_t> calibration_lane_stop_events_;
  std::vector<cudaEvent_t> calibration_lane_h2d_start_events_;
  std::vector<cudaEvent_t> calibration_lane_h2d_events_;
  bool pending_calibration_ = false;
  std::vector<std::size_t> pending_calibration_indices_;
  std::vector<unsigned char> pending_calibration_lane_used_;
  std::size_t pending_calibration_lane_count_ = 0;
  Clock::time_point pending_calibration_total_start_{};
  double pending_calibration_h2d_release_s_ = 0.0;
  double pending_calibration_h2d_event_sync_s_ = 0.0;
  double pending_calibration_h2d_event_elapsed_s_ = 0.0;
  float* d_warp_coverage_ = nullptr;
  float* d_warp_output_ = nullptr;
  float* d_warp_frame_coverage_ = nullptr;
  float* d_warp_inverse_ = nullptr;
  float* h_pinned_light_ = nullptr;
  cudaStream_t calibrate_stream_ = nullptr;
  cudaEvent_t calibrate_h2d_start_ = nullptr;
  cudaEvent_t calibrate_h2d_stop_ = nullptr;
  cudaEvent_t calibrate_kernel_start_ = nullptr;
  cudaEvent_t calibrate_kernel_stop_ = nullptr;
  bool has_bias_ = false;
  bool has_dark_ = false;
  bool has_flat_ = false;
};

}  // namespace

bool cuda_available() {
  int count = 0;
  const cudaError_t status = cudaGetDeviceCount(&count);
  return status == cudaSuccess && count > 0;
}

py::list list_devices() {
  int count = 0;
  check_cuda(cudaGetDeviceCount(&count), "cudaGetDeviceCount");
  py::list devices;
  for (int i = 0; i < count; ++i) {
    devices.append(device_info_dict(i));
  }
  return devices;
}

py::dict get_device_info(int device_id) {
  int count = 0;
  check_cuda(cudaGetDeviceCount(&count), "cudaGetDeviceCount");
  if (device_id < 0 || device_id >= count) {
    throw std::out_of_range("CUDA device id is out of range");
  }
  return device_info_dict(device_id);
}

py::array_t<float> smoke_add_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> a,
    py::array_t<float, py::array::c_style | py::array::forcecast> b) {
  const py::buffer_info a_info = a.request();
  const py::buffer_info b_info = b.request();
  require_same_shape(a_info, b_info);
  const std::size_t n = element_count(a_info);
  py::array_t<float> out(a_info.shape);
  const py::buffer_info out_info = out.request();

  float* d_a = nullptr;
  float* d_b = nullptr;
  float* d_out = nullptr;
  try {
    check_cuda(cudaMalloc(&d_a, n * sizeof(float)), "cudaMalloc(a)");
    check_cuda(cudaMalloc(&d_b, n * sizeof(float)), "cudaMalloc(b)");
    check_cuda(cudaMalloc(&d_out, n * sizeof(float)), "cudaMalloc(out)");
    check_cuda(cudaMemcpy(d_a, a_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(a)");
    check_cuda(cudaMemcpy(d_b, b_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(b)");
    glass_smoke_add_f32_launch(d_a, d_b, d_out, n);
    check_cuda(cudaGetLastError(), "smoke_add_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "smoke_add_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_info.ptr, d_out, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(out)");
  } catch (...) {
    cudaFree(d_a);
    cudaFree(d_b);
    cudaFree(d_out);
    throw;
  }
  cudaFree(d_a);
  cudaFree(d_b);
  cudaFree(d_out);
  return out;
}

float reduce_mean_tile_f32(py::array_t<float, py::array::c_style | py::array::forcecast> tile) {
  const py::buffer_info info = tile.request();
  const auto* ptr = static_cast<const float*>(info.ptr);
  const std::size_t n = element_count(info);
  if (n == 0) {
    throw std::invalid_argument("cannot reduce an empty tile");
  }
  double sum = 0.0;
  for (std::size_t i = 0; i < n; ++i) {
    sum += ptr[i];
  }
  return static_cast<float>(sum / static_cast<double>(n));
}

py::array_t<float> calibrate_tile_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> light,
    py::object bias_obj,
    py::object dark_obj,
    py::object flat_obj,
    float light_exposure_s,
    py::object dark_exposure_obj,
    py::object policy_obj) {
  const py::buffer_info light_info = light.request();
  const std::size_t n = element_count(light_info);
  py::array_t<float> out(light_info.shape);
  const py::buffer_info out_info = out.request();

  py::array_t<float, py::array::c_style | py::array::forcecast> bias;
  py::array_t<float, py::array::c_style | py::array::forcecast> dark;
  py::array_t<float, py::array::c_style | py::array::forcecast> flat;
  py::buffer_info bias_info;
  py::buffer_info dark_info;
  py::buffer_info flat_info;

  const bool has_bias = !bias_obj.is_none();
  const bool has_dark = !dark_obj.is_none();
  const bool has_flat = !flat_obj.is_none();

  if (has_bias) {
    bias = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(bias_obj);
    bias_info = bias.request();
    require_same_shape(light_info, bias_info);
  }
  if (has_dark) {
    dark = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(dark_obj);
    dark_info = dark.request();
    require_same_shape(light_info, dark_info);
  }
  if (has_flat) {
    flat = py::cast<py::array_t<float, py::array::c_style | py::array::forcecast>>(flat_obj);
    flat_info = flat.request();
    require_same_shape(light_info, flat_info);
  }

  py::dict policy;
  if (!policy_obj.is_none()) {
    policy = py::cast<py::dict>(policy_obj);
  }
  const bool master_dark_includes_bias =
      dict_bool(policy, "master_dark_includes_bias", true);
  const bool dark_scaling_enabled = dict_bool(policy, "dark_scaling_enabled", true);
  const float flat_floor = dict_float(policy, "flat_floor", 1.0e-6f);
  const float pedestal = dict_float(policy, "pedestal", 0.0f);

  float dark_scale = 1.0f;
  if (has_dark && dark_scaling_enabled && !dark_exposure_obj.is_none()) {
    const float dark_exposure_s = py::cast<float>(dark_exposure_obj);
    if (dark_exposure_s != 0.0f) {
      dark_scale = light_exposure_s / dark_exposure_s;
    }
  }

  float* d_light = nullptr;
  float* d_bias = nullptr;
  float* d_dark = nullptr;
  float* d_flat = nullptr;
  float* d_out = nullptr;

  try {
    check_cuda(cudaMalloc(&d_light, n * sizeof(float)), "cudaMalloc(light)");
    check_cuda(cudaMalloc(&d_out, n * sizeof(float)), "cudaMalloc(out)");
    check_cuda(
        cudaMemcpy(d_light, light_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(light)");
    if (has_bias) {
      check_cuda(cudaMalloc(&d_bias, n * sizeof(float)), "cudaMalloc(bias)");
      check_cuda(
          cudaMemcpy(d_bias, bias_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(bias)");
    }
    if (has_dark) {
      check_cuda(cudaMalloc(&d_dark, n * sizeof(float)), "cudaMalloc(dark)");
      check_cuda(
          cudaMemcpy(d_dark, dark_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(dark)");
    }
    if (has_flat) {
      check_cuda(cudaMalloc(&d_flat, n * sizeof(float)), "cudaMalloc(flat)");
      check_cuda(
          cudaMemcpy(d_flat, flat_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
          "cudaMemcpy(flat)");
    }
    glass_calibrate_tile_f32_launch(
        d_light,
        d_bias,
        d_dark,
        d_flat,
        d_out,
        n,
        has_bias,
        has_dark,
        has_flat,
        master_dark_includes_bias,
        dark_scale,
        flat_floor,
        pedestal);
    check_cuda(cudaGetLastError(), "calibrate_tile_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "calibrate_tile_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_info.ptr, d_out, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(calibrated)");
  } catch (...) {
    cudaFree(d_light);
    cudaFree(d_bias);
    cudaFree(d_dark);
    cudaFree(d_flat);
    cudaFree(d_out);
    throw;
  }

  cudaFree(d_light);
  cudaFree(d_bias);
  cudaFree(d_dark);
  cudaFree(d_flat);
  cudaFree(d_out);
  return out;
}

py::array_t<float> mean_stack_tiles_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> stack) {
  const py::buffer_info stack_info = stack.request();
  if (stack_info.ndim != 3) {
    throw std::invalid_argument("stack must have shape (frame_count, height, width)");
  }
  const auto frame_count = static_cast<std::size_t>(stack_info.shape[0]);
  const auto height = static_cast<py::ssize_t>(stack_info.shape[1]);
  const auto width = static_cast<py::ssize_t>(stack_info.shape[2]);
  if (frame_count == 0 || height <= 0 || width <= 0) {
    throw std::invalid_argument("stack dimensions must be non-empty");
  }
  const std::size_t pixels_per_frame = static_cast<std::size_t>(height * width);
  const std::size_t n = frame_count * pixels_per_frame;
  py::array_t<float> out({height, width});
  const py::buffer_info out_info = out.request();

  float* d_stack = nullptr;
  float* d_out = nullptr;
  try {
    check_cuda(cudaMalloc(&d_stack, n * sizeof(float)), "cudaMalloc(stack)");
    check_cuda(cudaMalloc(&d_out, pixels_per_frame * sizeof(float)), "cudaMalloc(out)");
    check_cuda(
        cudaMemcpy(d_stack, stack_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(stack)");
    glass_mean_stack_tiles_f32_launch(d_stack, d_out, frame_count, pixels_per_frame);
    check_cuda(cudaGetLastError(), "mean_stack_tiles_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "mean_stack_tiles_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_info.ptr, d_out, pixels_per_frame * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(mean tile)");
  } catch (...) {
    cudaFree(d_stack);
    cudaFree(d_out);
    throw;
  }

  cudaFree(d_stack);
  cudaFree(d_out);
  return out;
}

py::tuple warp_translation_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float dx,
    float dy,
    float fill) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(warp coverage)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(warp input)");
    glass_warp_translation_f32_launch(
        d_input,
        d_output,
        d_coverage,
        width,
        height,
        static_cast<int>(std::lround(dx)),
        static_cast<int>(std::lround(dy)),
        fill,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_translation_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_translation_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  return py::make_tuple(output, coverage);
}

py::tuple warp_translation_bilinear_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float dx,
    float dy,
    float fill) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(bilinear warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(bilinear warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(bilinear warp coverage)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(bilinear warp input)");
    glass_warp_translation_bilinear_f32_launch(
        d_input,
        d_output,
        d_coverage,
        width,
        height,
        dx,
        dy,
        fill,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_translation_bilinear_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_translation_bilinear_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(bilinear warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(bilinear warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  return py::make_tuple(output, coverage);
}

py::tuple warp_matrix_bilinear_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    py::object matrix_obj,
    float fill) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  float* d_inverse = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(matrix warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(matrix warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(matrix warp coverage)");
    check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(matrix warp inverse)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix warp input)");
    check_cuda(
        cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix warp inverse)");
    glass_warp_matrix_bilinear_f32_launch(
        d_input,
        d_output,
        d_coverage,
        d_inverse,
        width,
        height,
        fill,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_matrix_bilinear_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_matrix_bilinear_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    cudaFree(d_inverse);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  cudaFree(d_inverse);
  return py::make_tuple(output, coverage);
}

py::tuple warp_matrix_lanczos3_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    py::object matrix_obj,
    float fill,
    float clamping_threshold) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
  py::array_t<float> output({height, width});
  py::array_t<float> coverage({height, width});
  const py::buffer_info output_info = output.request();
  const py::buffer_info coverage_info = coverage.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_coverage = nullptr;
  float* d_inverse = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp output)");
    check_cuda(cudaMalloc(&d_coverage, n * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp coverage)");
    check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(matrix Lanczos3 warp inverse)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix Lanczos3 warp input)");
    check_cuda(
        cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix Lanczos3 warp inverse)");
    glass_warp_matrix_lanczos3_f32_launch(
        d_input,
        d_output,
        d_coverage,
        d_inverse,
        width,
        height,
        fill,
        clamping_threshold,
        nullptr);
    check_cuda(cudaGetLastError(), "warp_matrix_lanczos3_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "warp_matrix_lanczos3_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix Lanczos3 warp output)");
    check_cuda(
        cudaMemcpy(coverage_info.ptr, d_coverage, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix Lanczos3 warp coverage)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_coverage);
    cudaFree(d_inverse);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_coverage);
  cudaFree(d_inverse);
  return py::make_tuple(output, coverage);
}

py::dict matrix_alignment_metrics_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    py::object matrix_obj,
    int sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (sample_stride <= 0) {
    throw std::invalid_argument("sample_stride must be positive");
  }
  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  const int stride = sample_stride > 1 ? sample_stride : 1;
  const int sample_width = (width + stride - 1) / stride;
  const int sample_height = (height + stride - 1) / stride;
  const int sampled_pixels = sample_width * sample_height;
  const int blocks = std::max(1, std::min(1024, (sampled_pixels + 255) / 256));
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto inverse = invert_matrix3x3(parse_matrix3x3(matrix_obj));
  std::vector<double> partial_stats(static_cast<std::size_t>(blocks) * 7, 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  float* d_inverse = nullptr;
  double* d_partial_stats = nullptr;
  unsigned long long* d_partial_count = nullptr;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(matrix metrics reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(matrix metrics moving)");
    check_cuda(cudaMalloc(&d_inverse, inverse.size() * sizeof(float)), "cudaMalloc(matrix metrics inverse)");
    check_cuda(
        cudaMalloc(&d_partial_stats, partial_stats.size() * sizeof(double)),
        "cudaMalloc(matrix metrics partial stats)");
    check_cuda(
        cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
        "cudaMalloc(matrix metrics partial count)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix metrics reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix metrics moving)");
    check_cuda(
        cudaMemcpy(d_inverse, inverse.data(), inverse.size() * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix metrics inverse)");
    glass_matrix_alignment_metrics_f32_launch(
        d_reference,
        d_moving,
        d_inverse,
        d_partial_stats,
        d_partial_count,
        width,
        height,
        stride,
        blocks);
    check_cuda(cudaGetLastError(), "matrix_alignment_metrics_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "matrix_alignment_metrics_f32 synchronize");
    check_cuda(
        cudaMemcpy(partial_stats.data(), d_partial_stats, partial_stats.size() * sizeof(double), cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix metrics partial stats)");
    check_cuda(
        cudaMemcpy(
            partial_count.data(),
            d_partial_count,
            partial_count.size() * sizeof(unsigned long long),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(matrix metrics partial count)");
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    cudaFree(d_inverse);
    cudaFree(d_partial_stats);
    cudaFree(d_partial_count);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);
  cudaFree(d_inverse);
  cudaFree(d_partial_stats);
  cudaFree(d_partial_count);

  double sum_ref = 0.0;
  double sum_mov = 0.0;
  double sum_ref2 = 0.0;
  double sum_mov2 = 0.0;
  double sum_cross = 0.0;
  double sum_diff2 = 0.0;
  double sum_abs_diff = 0.0;
  unsigned long long valid_pixels = 0ULL;
  for (int block = 0; block < blocks; ++block) {
    const std::size_t offset = static_cast<std::size_t>(block) * 7;
    sum_ref += partial_stats[offset + 0];
    sum_mov += partial_stats[offset + 1];
    sum_ref2 += partial_stats[offset + 2];
    sum_mov2 += partial_stats[offset + 3];
    sum_cross += partial_stats[offset + 4];
    sum_diff2 += partial_stats[offset + 5];
    sum_abs_diff += partial_stats[offset + 6];
    valid_pixels += partial_count[static_cast<std::size_t>(block)];
  }

  const double count = static_cast<double>(valid_pixels);
  double rms = std::numeric_limits<double>::quiet_NaN();
  double mean_abs_diff = std::numeric_limits<double>::quiet_NaN();
  double ncc = std::numeric_limits<double>::quiet_NaN();
  if (valid_pixels > 0ULL) {
    rms = std::sqrt(sum_diff2 / count);
    mean_abs_diff = sum_abs_diff / count;
  }
  if (valid_pixels > 1ULL) {
    const double numerator = sum_cross - (sum_ref * sum_mov / count);
    const double ref_var = std::max(sum_ref2 - (sum_ref * sum_ref / count), 0.0);
    const double mov_var = std::max(sum_mov2 - (sum_mov * sum_mov / count), 0.0);
    const double denominator = std::sqrt(ref_var * mov_var);
    if (denominator > 0.0) {
      ncc = numerator / denominator;
    }
  }

  py::dict result;
  result["valid_pixels"] = valid_pixels;
  result["sampled_pixels"] = sampled_pixels;
  result["sample_stride"] = stride;
  result["rms"] = rms;
  result["mean_abs_diff"] = mean_abs_diff;
  result["ncc"] = ncc;
  result["model"] = "matrix_alignment_metrics_cuda";
  return result;
}

py::dict refine_matrix_translation_with_metrics_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    py::object matrix_obj,
    float search_radius_px,
    float coarse_step_px,
    float fine_radius_px,
    float fine_step_px,
    int coarse_sample_stride,
    int final_sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
    throw std::invalid_argument("search radii must be non-negative");
  }
  if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
    throw std::invalid_argument("search steps must be positive");
  }
  if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
    throw std::invalid_argument("sample strides must be positive");
  }

  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto base_matrix = parse_matrix3x3(matrix_obj);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  MatrixCandidateMetrics coarse_best;
  MatrixCandidateMetrics best;
  int coarse_candidates = 0;
  int fine_candidates = 0;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(matrix refine reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(matrix refine moving)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix refine reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix refine moving)");

    const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
    coarse_candidates = static_cast<int>(coarse_offsets.size());
    coarse_best = score_matrix_translation_candidates_f32(
        d_reference,
        d_moving,
        base_matrix,
        coarse_offsets,
        width,
        height,
        coarse_sample_stride);
    best = coarse_best;

    if (fine_radius_px > 0.0f) {
      const auto fine_offsets = translation_offsets(coarse_best.dx, coarse_best.dy, fine_radius_px, fine_step_px);
      fine_candidates = static_cast<int>(fine_offsets.size());
      best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          fine_offsets,
          width,
          height,
          final_sample_stride);
    } else if (final_sample_stride != coarse_sample_stride) {
      const std::vector<std::pair<float, float>> final_offsets{{coarse_best.dx, coarse_best.dy}};
      best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          final_offsets,
          width,
          height,
          final_sample_stride);
    }
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list values;
    for (int col = 0; col < 3; ++col) {
      values.append(best.matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(values);
  }

  py::dict result;
  result["matrix"] = matrix_rows;
  result["dx_correction"] = best.dx;
  result["dy_correction"] = best.dy;
  result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
  result["coarse_candidates"] = coarse_candidates;
  result["fine_candidates"] = fine_candidates;
  result["search_radius_px"] = search_radius_px;
  result["coarse_step_px"] = coarse_step_px;
  result["fine_radius_px"] = fine_radius_px;
  result["fine_step_px"] = fine_step_px;
  result["coarse_sample_stride"] = coarse_sample_stride;
  result["final_sample_stride"] = final_sample_stride;
  result["model"] = "cuda_matrix_metric_translation_refine_grid";
  return result;
}

py::dict refine_matrix_translation_candidates_with_metrics_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    py::object matrices_obj,
    float search_radius_px,
    float coarse_step_px,
    float fine_radius_px,
    float fine_step_px,
    int coarse_sample_stride,
    int final_sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (search_radius_px < 0.0f || fine_radius_px < 0.0f) {
    throw std::invalid_argument("search radii must be non-negative");
  }
  if (coarse_step_px <= 0.0f || fine_step_px <= 0.0f) {
    throw std::invalid_argument("search steps must be positive");
  }
  if (coarse_sample_stride <= 0 || final_sample_stride <= 0) {
    throw std::invalid_argument("sample strides must be positive");
  }

  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const auto seed_matrices = parse_matrix_stack(matrices_obj);
  const auto coarse_offsets = translation_offsets(0.0f, 0.0f, search_radius_px, coarse_step_px);
  const int coarse_candidates = static_cast<int>(coarse_offsets.size());

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  MatrixCandidateMetrics best;
  bool have_best = false;
  int selected_index = -1;
  py::list seed_results;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(matrix multi-refine reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(matrix multi-refine moving)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix multi-refine reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(matrix multi-refine moving)");

    for (std::size_t seed_index = 0; seed_index < seed_matrices.size(); ++seed_index) {
      const auto& base_matrix = seed_matrices[seed_index];
      const MatrixCandidateMetrics coarse_best = score_matrix_translation_candidates_f32(
          d_reference,
          d_moving,
          base_matrix,
          coarse_offsets,
          width,
          height,
          coarse_sample_stride);
      MatrixCandidateMetrics seed_best = coarse_best;
      int fine_candidates = 0;
      if (fine_radius_px > 0.0f) {
        const auto fine_offsets = translation_offsets(coarse_best.dx, coarse_best.dy, fine_radius_px, fine_step_px);
        fine_candidates = static_cast<int>(fine_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            fine_offsets,
            width,
            height,
            final_sample_stride);
      } else if (final_sample_stride != coarse_sample_stride) {
        const std::vector<std::pair<float, float>> final_offsets{{coarse_best.dx, coarse_best.dy}};
        fine_candidates = static_cast<int>(final_offsets.size());
        seed_best = score_matrix_translation_candidates_f32(
            d_reference,
            d_moving,
            base_matrix,
            final_offsets,
            width,
            height,
            final_sample_stride);
      }

      py::dict seed_result;
      seed_result["seed_index"] = static_cast<int>(seed_index);
      seed_result["matrix"] = matrix3x3_to_pylist(seed_best.matrix);
      seed_result["dx_correction"] = seed_best.dx;
      seed_result["dy_correction"] = seed_best.dy;
      seed_result["metrics"] = matrix_candidate_to_dict(seed_best, "matrix_alignment_metrics_cuda_candidate_grid");
      seed_result["coarse_candidates"] = coarse_candidates;
      seed_result["fine_candidates"] = fine_candidates;
      seed_results.append(seed_result);

      if (!have_best || better_matrix_metric(seed_best, best)) {
        best = seed_best;
        selected_index = static_cast<int>(seed_index);
        have_best = true;
      }
    }
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);

  if (!have_best) {
    throw std::runtime_error("matrix multi-refine produced no candidates");
  }
  py::dict result;
  result["matrix"] = matrix3x3_to_pylist(best.matrix);
  result["dx_correction"] = best.dx;
  result["dy_correction"] = best.dy;
  result["metrics"] = matrix_candidate_to_dict(best, "matrix_alignment_metrics_cuda_candidate_grid");
  result["selected_index"] = selected_index;
  result["seed_count"] = static_cast<int>(seed_matrices.size());
  result["seed_results"] = seed_results;
  result["coarse_candidates_per_seed"] = coarse_candidates;
  result["search_radius_px"] = search_radius_px;
  result["coarse_step_px"] = coarse_step_px;
  result["fine_radius_px"] = fine_radius_px;
  result["fine_step_px"] = fine_step_px;
  result["coarse_sample_stride"] = coarse_sample_stride;
  result["final_sample_stride"] = final_sample_stride;
  result["model"] = "cuda_matrix_metric_translation_multi_seed_refine_grid";
  return result;
}

py::dict estimate_translation_search_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    int max_shift_x,
    int max_shift_y,
    int sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (max_shift_x < 0 || max_shift_y < 0) {
    throw std::invalid_argument("max_shift values must be non-negative");
  }
  if (sample_stride <= 0) {
    throw std::invalid_argument("sample_stride must be positive");
  }
  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  if (height <= 0 || width <= 0) {
    throw std::invalid_argument("reference and moving images must be non-empty");
  }
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const int shift_count = (2 * max_shift_x + 1) * (2 * max_shift_y + 1);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  float* d_scores = nullptr;
  int* d_best_dx = nullptr;
  int* d_best_dy = nullptr;
  float* d_best_score = nullptr;
  int best_dx = 0;
  int best_dy = 0;
  float best_score = 0.0f;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(registration reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(registration moving)");
    check_cuda(
        cudaMalloc(&d_scores, static_cast<std::size_t>(shift_count) * sizeof(float)),
        "cudaMalloc(registration scores)");
    check_cuda(cudaMalloc(&d_best_dx, sizeof(int)), "cudaMalloc(registration best dx)");
    check_cuda(cudaMalloc(&d_best_dy, sizeof(int)), "cudaMalloc(registration best dy)");
    check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(registration best score)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(registration reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(registration moving)");
    glass_estimate_translation_search_f32_launch(
        d_reference,
        d_moving,
        d_scores,
        d_best_dx,
        d_best_dy,
        d_best_score,
        width,
        height,
        max_shift_x,
        max_shift_y,
        sample_stride);
    check_cuda(cudaGetLastError(), "estimate_translation_search_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_translation_search_f32 synchronize");
    check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(best dx)");
    check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(best dy)");
    check_cuda(
        cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(best score)");
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);
  cudaFree(d_scores);
  cudaFree(d_best_dx);
  cudaFree(d_best_dy);
  cudaFree(d_best_score);

  py::dict result;
  result["dx"] = best_dx;
  result["dy"] = best_dy;
  result["score"] = best_score;
  result["search_count"] = shift_count;
  result["sample_stride"] = sample_stride;
  result["model"] = "translation_integer_ncc";
  return result;
}

py::dict estimate_translation_subpixel_ncc_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving,
    float center_dx,
    float center_dy,
    int radius_steps,
    float step,
    int sample_stride) {
  const py::buffer_info reference_info = reference.request();
  const py::buffer_info moving_info = moving.request();
  if (reference_info.ndim != 2 || moving_info.ndim != 2) {
    throw std::invalid_argument("reference and moving must have shape (height, width)");
  }
  require_same_shape(reference_info, moving_info);
  if (radius_steps < 0) {
    throw std::invalid_argument("radius_steps must be non-negative");
  }
  if (step <= 0.0f) {
    throw std::invalid_argument("step must be positive");
  }
  if (sample_stride <= 0) {
    throw std::invalid_argument("sample_stride must be positive");
  }
  const int height = static_cast<int>(reference_info.shape[0]);
  const int width = static_cast<int>(reference_info.shape[1]);
  if (height <= 0 || width <= 0) {
    throw std::invalid_argument("reference and moving images must be non-empty");
  }
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const int candidate_count = (2 * radius_steps + 1) * (2 * radius_steps + 1);

  float* d_reference = nullptr;
  float* d_moving = nullptr;
  float* d_scores = nullptr;
  float* d_best_dx = nullptr;
  float* d_best_dy = nullptr;
  float* d_best_score = nullptr;
  float best_dx = 0.0f;
  float best_dy = 0.0f;
  float best_score = 0.0f;
  try {
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(subpixel reference)");
    check_cuda(cudaMalloc(&d_moving, n * sizeof(float)), "cudaMalloc(subpixel moving)");
    check_cuda(
        cudaMalloc(&d_scores, static_cast<std::size_t>(candidate_count) * sizeof(float)),
        "cudaMalloc(subpixel scores)");
    check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(subpixel best dx)");
    check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(subpixel best dy)");
    check_cuda(cudaMalloc(&d_best_score, sizeof(float)), "cudaMalloc(subpixel best score)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(subpixel reference)");
    check_cuda(
        cudaMemcpy(d_moving, moving_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(subpixel moving)");
    glass_estimate_translation_subpixel_ncc_f32_launch(
        d_reference,
        d_moving,
        d_scores,
        d_best_dx,
        d_best_dy,
        d_best_score,
        width,
        height,
        center_dx,
        center_dy,
        radius_steps,
        step,
        sample_stride);
    check_cuda(cudaGetLastError(), "estimate_translation_subpixel_ncc_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_translation_subpixel_ncc_f32 synchronize");
    check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(subpixel best dx)");
    check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(subpixel best dy)");
    check_cuda(
        cudaMemcpy(&best_score, d_best_score, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(subpixel best score)");
  } catch (...) {
    cudaFree(d_reference);
    cudaFree(d_moving);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_score);
    throw;
  }
  cudaFree(d_reference);
  cudaFree(d_moving);
  cudaFree(d_scores);
  cudaFree(d_best_dx);
  cudaFree(d_best_dy);
  cudaFree(d_best_score);

  py::dict result;
  result["dx"] = best_dx;
  result["dy"] = best_dy;
  result["score"] = best_score;
  result["candidate_count"] = candidate_count;
  result["center_dx"] = center_dx;
  result["center_dy"] = center_dy;
  result["radius_steps"] = radius_steps;
  result["step"] = step;
  result["sample_stride"] = sample_stride;
  result["model"] = "translation_subpixel_ncc";
  return result;
}

py::dict estimate_translation_from_catalogs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    float tolerance_px,
    float max_abs_dx,
    float max_abs_dy,
    float prior_dx,
    float prior_dy,
    float prior_radius_px) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(moving_x_info, moving_y_info);
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int moving_count = static_cast<int>(moving_x_info.shape[0]);
  if (reference_count <= 0 || moving_count <= 0) {
    throw std::invalid_argument("catalogs must be non-empty");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (max_abs_dx < 0.0f) {
    max_abs_dx = -1.0f;
  }
  if (max_abs_dy < 0.0f) {
    max_abs_dy = max_abs_dx;
  }
  if (prior_radius_px < 0.0f) {
    prior_radius_px = -1.0f;
  }
  const int pair_count = reference_count * moving_count;

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_candidate_dx = nullptr;
  float* d_candidate_dy = nullptr;
  int* d_scores = nullptr;
  float* d_best_dx = nullptr;
  float* d_best_dy = nullptr;
  int* d_best_inliers = nullptr;
  int* d_moving_best_reference = nullptr;
  int* d_reference_best_moving = nullptr;
  float* d_refine_sums = nullptr;
  int* d_mutual_inliers = nullptr;
  float* d_refined_dx = nullptr;
  float* d_refined_dy = nullptr;
  float* d_rms_px = nullptr;
  float best_dx = 0.0f;
  float best_dy = 0.0f;
  int best_inliers = 0;
  int mutual_inliers = 0;
  float refined_dx = 0.0f;
  float refined_dy = 0.0f;
  float rms_px = 0.0f;
  try {
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(catalog reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(catalog reference y)");
    check_cuda(
        cudaMalloc(&d_moving_x, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(catalog moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(catalog moving y)");
    check_cuda(
        cudaMalloc(&d_candidate_dx, static_cast<std::size_t>(pair_count) * sizeof(float)),
        "cudaMalloc(catalog candidate dx)");
    check_cuda(
        cudaMalloc(&d_candidate_dy, static_cast<std::size_t>(pair_count) * sizeof(float)),
        "cudaMalloc(catalog candidate dy)");
    check_cuda(cudaMalloc(&d_scores, static_cast<std::size_t>(pair_count) * sizeof(int)), "cudaMalloc(catalog scores)");
    check_cuda(cudaMalloc(&d_best_dx, sizeof(float)), "cudaMalloc(catalog best dx)");
    check_cuda(cudaMalloc(&d_best_dy, sizeof(float)), "cudaMalloc(catalog best dy)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(catalog best inliers)");
    check_cuda(
        cudaMalloc(&d_moving_best_reference, static_cast<std::size_t>(moving_count) * sizeof(int)),
        "cudaMalloc(catalog moving best reference)");
    check_cuda(
        cudaMalloc(&d_reference_best_moving, static_cast<std::size_t>(reference_count) * sizeof(int)),
        "cudaMalloc(catalog reference best moving)");
    check_cuda(cudaMalloc(&d_refine_sums, 3 * sizeof(float)), "cudaMalloc(catalog refine sums)");
    check_cuda(cudaMalloc(&d_mutual_inliers, sizeof(int)), "cudaMalloc(catalog mutual inliers)");
    check_cuda(cudaMalloc(&d_refined_dx, sizeof(float)), "cudaMalloc(catalog refined dx)");
    check_cuda(cudaMalloc(&d_refined_dy, sizeof(float)), "cudaMalloc(catalog refined dy)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(catalog rms)");
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog reference y)");
    check_cuda(
        cudaMemcpy(
            d_moving_x,
            moving_x_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog moving x)");
    check_cuda(
        cudaMemcpy(
            d_moving_y,
            moving_y_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(catalog moving y)");
    glass_estimate_translation_from_catalogs_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_candidate_dx,
        d_candidate_dy,
        d_scores,
        d_best_dx,
        d_best_dy,
        d_best_inliers,
        d_moving_best_reference,
        d_reference_best_moving,
        d_refine_sums,
        d_mutual_inliers,
        d_refined_dx,
        d_refined_dy,
        d_rms_px,
        reference_count,
        moving_count,
        tolerance_px,
        max_abs_dx,
        max_abs_dy,
        prior_dx,
        prior_dy,
        prior_radius_px);
    check_cuda(cudaGetLastError(), "estimate_translation_from_catalogs_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_translation_from_catalogs_f32 synchronize");
    check_cuda(cudaMemcpy(&best_dx, d_best_dx, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(catalog best dx)");
    check_cuda(cudaMemcpy(&best_dy, d_best_dy, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(catalog best dy)");
    check_cuda(
        cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog best inliers)");
    check_cuda(
        cudaMemcpy(&mutual_inliers, d_mutual_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog mutual inliers)");
    check_cuda(
        cudaMemcpy(&refined_dx, d_refined_dx, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog refined dx)");
    check_cuda(
        cudaMemcpy(&refined_dy, d_refined_dy, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(catalog refined dy)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(catalog rms)");
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_candidate_dx);
    cudaFree(d_candidate_dy);
    cudaFree(d_scores);
    cudaFree(d_best_dx);
    cudaFree(d_best_dy);
    cudaFree(d_best_inliers);
    cudaFree(d_moving_best_reference);
    cudaFree(d_reference_best_moving);
    cudaFree(d_refine_sums);
    cudaFree(d_mutual_inliers);
    cudaFree(d_refined_dx);
    cudaFree(d_refined_dy);
    cudaFree(d_rms_px);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_candidate_dx);
  cudaFree(d_candidate_dy);
  cudaFree(d_scores);
  cudaFree(d_best_dx);
  cudaFree(d_best_dy);
  cudaFree(d_best_inliers);
  cudaFree(d_moving_best_reference);
  cudaFree(d_reference_best_moving);
  cudaFree(d_refine_sums);
  cudaFree(d_mutual_inliers);
  cudaFree(d_refined_dx);
  cudaFree(d_refined_dy);
  cudaFree(d_rms_px);

  py::dict result;
  result["dx"] = best_dx;
  result["dy"] = best_dy;
  result["inliers"] = best_inliers;
  result["refined_dx"] = refined_dx;
  result["refined_dy"] = refined_dy;
  result["mutual_inliers"] = mutual_inliers;
  result["rms_px"] = rms_px;
  result["candidate_count"] = pair_count;
  result["reference_count"] = reference_count;
  result["moving_count"] = moving_count;
  result["tolerance_px"] = tolerance_px;
  result["max_abs_dx"] = max_abs_dx;
  result["max_abs_dy"] = max_abs_dy;
  result["prior_dx"] = prior_dx;
  result["prior_dy"] = prior_dy;
  result["prior_radius_px"] = prior_radius_px;
  result["model"] = "catalog_pair_offset_translation";
  return result;
}

py::dict estimate_similarity_from_pairs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("matched coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(reference_x_info, moving_x_info);
  require_same_shape(reference_x_info, moving_y_info);
  const int count = static_cast<int>(reference_x_info.shape[0]);
  if (count <= 0) {
    throw std::invalid_argument("matched coordinate arrays must be non-empty");
  }

  constexpr int threads = 256;
  const int blocks = std::min(4096, std::max(1, (count + threads - 1) / threads));
  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_valid_count = nullptr;
  int* d_status = nullptr;
  double* d_partial_sums = nullptr;
  unsigned long long* d_partial_count = nullptr;
  double* d_partial_residual_sums = nullptr;
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int valid_count = 0;
  int status = 1;

  try {
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity reference y)");
    check_cuda(
        cudaMalloc(&d_moving_x, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, static_cast<std::size_t>(count) * sizeof(float)),
        "cudaMalloc(similarity moving y)");
    check_cuda(cudaMalloc(&d_matrix, host_matrix.size() * sizeof(float)), "cudaMalloc(similarity matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(similarity scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(similarity rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(similarity rms)");
    check_cuda(cudaMalloc(&d_valid_count, sizeof(int)), "cudaMalloc(similarity valid count)");
    check_cuda(cudaMalloc(&d_status, sizeof(int)), "cudaMalloc(similarity status)");
    check_cuda(
        cudaMalloc(&d_partial_sums, static_cast<std::size_t>(blocks) * 7 * sizeof(double)),
        "cudaMalloc(similarity partial sums)");
    check_cuda(
        cudaMalloc(&d_partial_count, static_cast<std::size_t>(blocks) * sizeof(unsigned long long)),
        "cudaMalloc(similarity partial count)");
    check_cuda(
        cudaMalloc(&d_partial_residual_sums, static_cast<std::size_t>(blocks) * sizeof(double)),
        "cudaMalloc(similarity partial residual sums)");
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity reference y)");
    check_cuda(
        cudaMemcpy(
            d_moving_x,
            moving_x_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity moving x)");
    check_cuda(
        cudaMemcpy(
            d_moving_y,
            moving_y_info.ptr,
            static_cast<std::size_t>(count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity moving y)");
    glass_estimate_similarity_from_pairs_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_matrix,
        d_scale,
        d_rotation_rad,
        d_rms_px,
        d_valid_count,
        d_status,
        d_partial_sums,
        d_partial_count,
        d_partial_residual_sums,
        count,
        blocks);
    check_cuda(cudaGetLastError(), "estimate_similarity_from_pairs_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_pairs_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity matrix)");
    check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity scale)");
    check_cuda(
        cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity rotation)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity rms)");
    check_cuda(
        cudaMemcpy(&valid_count, d_valid_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity valid count)");
    check_cuda(cudaMemcpy(&status, d_status, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity status)");
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_valid_count);
    cudaFree(d_status);
    cudaFree(d_partial_sums);
    cudaFree(d_partial_count);
    cudaFree(d_partial_residual_sums);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_valid_count);
  cudaFree(d_status);
  cudaFree(d_partial_sums);
  cudaFree(d_partial_count);
  cudaFree(d_partial_residual_sums);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list matrix_row;
    for (int col = 0; col < 3; ++col) {
      matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(matrix_row);
  }
  py::dict result;
  result["matrix"] = matrix_rows;
  result["scale"] = scale;
  result["rotation_rad"] = rotation_rad;
  result["rms_px"] = rms_px;
  result["valid_pairs"] = valid_count;
  result["input_pairs"] = count;
  result["status"] = status == 0 ? "ok" : "failed";
  result["status_code"] = status;
  result["model"] = "matched_pair_similarity_cuda";
  return result;
}

py::dict triangle_asterism_descriptors_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> x,
    py::array_t<float, py::array::c_style | py::array::forcecast> y,
    int max_stars,
    int neighbors,
    int max_descriptors) {
  const py::buffer_info x_info = x.request();
  const py::buffer_info y_info = y.request();
  if (x_info.ndim != 1 || y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(x_info, y_info);
  if (max_stars < 0) {
    throw std::invalid_argument("max_stars must be non-negative");
  }
  if (max_descriptors < 0) {
    throw std::invalid_argument("max_descriptors must be non-negative");
  }
  const int input_count = static_cast<int>(x_info.shape[0]);
  const int count = std::min(input_count, max_stars);
  int neighbor_count = std::min(count, neighbors);
  neighbor_count = std::max(3, neighbor_count);
  neighbor_count = std::min(16, neighbor_count);
  const int combos_per_anchor = neighbor_count * (neighbor_count - 1) * (neighbor_count - 2) / 6;
  const int raw_count = count >= 3 ? count * combos_per_anchor : 0;

  py::array_t<float> descriptor_array({0, 2});
  py::array_t<int> index_array({0, 3});
  py::array_t<float> area_array({0});
  py::dict empty_result;
  if (count < 3 || max_descriptors == 0 || raw_count == 0) {
    empty_result["count"] = 0;
    empty_result["raw_count"] = raw_count;
    empty_result["max_stars"] = max_stars;
    empty_result["neighbors"] = neighbor_count;
    empty_result["descriptors"] = descriptor_array;
    empty_result["indices"] = index_array;
    empty_result["areas"] = area_array;
    empty_result["model"] = "triangle_asterism_descriptors_cuda";
    return empty_result;
  }

  float* d_x = nullptr;
  float* d_y = nullptr;
  float* d_descriptors = nullptr;
  int* d_indices = nullptr;
  float* d_areas = nullptr;
  unsigned char* d_valid = nullptr;
  std::vector<float> host_descriptors(static_cast<std::size_t>(raw_count) * 2, std::numeric_limits<float>::quiet_NaN());
  std::vector<int> host_indices(static_cast<std::size_t>(raw_count) * 3, -1);
  std::vector<float> host_areas(static_cast<std::size_t>(raw_count), std::numeric_limits<float>::quiet_NaN());
  std::vector<unsigned char> host_valid(static_cast<std::size_t>(raw_count), 0);
  try {
    check_cuda(cudaMalloc(&d_x, static_cast<std::size_t>(count) * sizeof(float)), "cudaMalloc(triangle x)");
    check_cuda(cudaMalloc(&d_y, static_cast<std::size_t>(count) * sizeof(float)), "cudaMalloc(triangle y)");
    check_cuda(
        cudaMalloc(&d_descriptors, static_cast<std::size_t>(raw_count) * 2 * sizeof(float)),
        "cudaMalloc(triangle descriptors)");
    check_cuda(
        cudaMalloc(&d_indices, static_cast<std::size_t>(raw_count) * 3 * sizeof(int)),
        "cudaMalloc(triangle indices)");
    check_cuda(cudaMalloc(&d_areas, static_cast<std::size_t>(raw_count) * sizeof(float)), "cudaMalloc(triangle areas)");
    check_cuda(cudaMalloc(&d_valid, static_cast<std::size_t>(raw_count) * sizeof(unsigned char)), "cudaMalloc(triangle valid)");
    check_cuda(cudaMemcpy(d_x, x_info.ptr, static_cast<std::size_t>(count) * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(triangle x)");
    check_cuda(cudaMemcpy(d_y, y_info.ptr, static_cast<std::size_t>(count) * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(triangle y)");
    glass_triangle_asterism_descriptors_f32_launch(
        d_x,
        d_y,
        d_descriptors,
        d_indices,
        d_areas,
        d_valid,
        count,
        neighbor_count,
        raw_count);
    check_cuda(cudaGetLastError(), "triangle_asterism_descriptors_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "triangle_asterism_descriptors_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_descriptors.data(), d_descriptors, host_descriptors.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle descriptors)");
    check_cuda(
        cudaMemcpy(host_indices.data(), d_indices, host_indices.size() * sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle indices)");
    check_cuda(
        cudaMemcpy(host_areas.data(), d_areas, host_areas.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle areas)");
    check_cuda(
        cudaMemcpy(host_valid.data(), d_valid, host_valid.size() * sizeof(unsigned char), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle valid)");
  } catch (...) {
    cudaFree(d_x);
    cudaFree(d_y);
    cudaFree(d_descriptors);
    cudaFree(d_indices);
    cudaFree(d_areas);
    cudaFree(d_valid);
    throw;
  }
  cudaFree(d_x);
  cudaFree(d_y);
  cudaFree(d_descriptors);
  cudaFree(d_indices);
  cudaFree(d_areas);
  cudaFree(d_valid);

  struct TriangleDescriptor {
    int key0;
    int key1;
    int key2;
    float descriptor0;
    float descriptor1;
    int index0;
    int index1;
    int index2;
    float area;
  };
  std::vector<TriangleDescriptor> triangles;
  triangles.reserve(static_cast<std::size_t>(raw_count));
  for (int slot = 0; slot < raw_count; ++slot) {
    if (host_valid[static_cast<std::size_t>(slot)] == 0) {
      continue;
    }
    int index0 = host_indices[static_cast<std::size_t>(slot) * 3 + 0];
    int index1 = host_indices[static_cast<std::size_t>(slot) * 3 + 1];
    int index2 = host_indices[static_cast<std::size_t>(slot) * 3 + 2];
    if (index0 < 0 || index1 < 0 || index2 < 0) {
      continue;
    }
    std::array<int, 3> key{index0, index1, index2};
    std::sort(key.begin(), key.end());
    triangles.push_back(
        TriangleDescriptor{
            key[0],
            key[1],
            key[2],
            host_descriptors[static_cast<std::size_t>(slot) * 2 + 0],
            host_descriptors[static_cast<std::size_t>(slot) * 2 + 1],
            index0,
            index1,
            index2,
            host_areas[static_cast<std::size_t>(slot)]});
  }
  std::sort(triangles.begin(), triangles.end(), [](const TriangleDescriptor& left, const TriangleDescriptor& right) {
    if (left.key0 != right.key0) {
      return left.key0 < right.key0;
    }
    if (left.key1 != right.key1) {
      return left.key1 < right.key1;
    }
    return left.key2 < right.key2;
  });
  std::vector<TriangleDescriptor> unique_triangles;
  unique_triangles.reserve(triangles.size());
  for (const auto& triangle : triangles) {
    if (!unique_triangles.empty()) {
      const auto& previous = unique_triangles.back();
      if (previous.key0 == triangle.key0 && previous.key1 == triangle.key1 && previous.key2 == triangle.key2) {
        continue;
      }
    }
    unique_triangles.push_back(triangle);
  }
  std::sort(
      unique_triangles.begin(),
      unique_triangles.end(),
      [](const TriangleDescriptor& left, const TriangleDescriptor& right) {
        if (left.area != right.area) {
          return left.area > right.area;
        }
        if (left.key0 != right.key0) {
          return left.key0 < right.key0;
        }
        if (left.key1 != right.key1) {
          return left.key1 < right.key1;
        }
        return left.key2 < right.key2;
      });

  const int output_count =
      std::min(static_cast<int>(unique_triangles.size()), max_descriptors);
  descriptor_array = py::array_t<float>({output_count, 2});
  index_array = py::array_t<int>({output_count, 3});
  area_array = py::array_t<float>({output_count});
  auto descriptor_info = descriptor_array.request();
  auto index_info = index_array.request();
  auto area_info = area_array.request();
  float* descriptor_ptr = static_cast<float*>(descriptor_info.ptr);
  int* index_ptr = static_cast<int*>(index_info.ptr);
  float* area_ptr = static_cast<float*>(area_info.ptr);
  for (int i = 0; i < output_count; ++i) {
    const auto& triangle = unique_triangles[static_cast<std::size_t>(i)];
    descriptor_ptr[i * 2 + 0] = triangle.descriptor0;
    descriptor_ptr[i * 2 + 1] = triangle.descriptor1;
    index_ptr[i * 3 + 0] = triangle.index0;
    index_ptr[i * 3 + 1] = triangle.index1;
    index_ptr[i * 3 + 2] = triangle.index2;
    area_ptr[i] = triangle.area;
  }

  py::dict result;
  result["count"] = output_count;
  result["raw_count"] = raw_count;
  result["max_stars"] = max_stars;
  result["neighbors"] = neighbor_count;
  result["descriptors"] = descriptor_array;
  result["indices"] = index_array;
  result["areas"] = area_array;
  result["model"] = "triangle_asterism_descriptors_cuda";
  return result;
}

py::list triangle_asterism_descriptors_batch_f32(
    py::sequence x_list,
    py::sequence y_list,
    int max_stars,
    int neighbors,
    int max_descriptors) {
  const auto total_start = Clock::now();
  const py::ssize_t batch_count_py = py::len(x_list);
  if (py::len(y_list) != batch_count_py) {
    throw std::invalid_argument("catalog x/y batch lists must have the same length");
  }
  if (max_stars < 0) {
    throw std::invalid_argument("max_stars must be non-negative");
  }
  if (max_descriptors < 0) {
    throw std::invalid_argument("max_descriptors must be non-negative");
  }
  py::list results;
  if (batch_count_py == 0) {
    return results;
  }

  using FloatArray = py::array_t<float, py::array::c_style | py::array::forcecast>;
  std::vector<FloatArray> x_arrays;
  std::vector<FloatArray> y_arrays;
  std::vector<int> counts;
  std::vector<int> neighbor_counts;
  std::vector<int> combos_per_frame;
  std::vector<int> raw_counts;
  x_arrays.reserve(static_cast<std::size_t>(batch_count_py));
  y_arrays.reserve(static_cast<std::size_t>(batch_count_py));
  counts.reserve(static_cast<std::size_t>(batch_count_py));
  neighbor_counts.reserve(static_cast<std::size_t>(batch_count_py));
  combos_per_frame.reserve(static_cast<std::size_t>(batch_count_py));
  raw_counts.reserve(static_cast<std::size_t>(batch_count_py));

  int max_count = 0;
  int raw_capacity = 0;
  const auto host_prepare_start = Clock::now();
  for (py::ssize_t batch_index = 0; batch_index < batch_count_py; ++batch_index) {
    auto x = FloatArray::ensure(x_list[batch_index]);
    auto y = FloatArray::ensure(y_list[batch_index]);
    if (!x || !y) {
      throw std::invalid_argument("catalog batch items must be convertible to float arrays");
    }
    const py::buffer_info x_info = x.request();
    const py::buffer_info y_info = y.request();
    if (x_info.ndim != 1 || y_info.ndim != 1) {
      throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
    }
    require_same_shape(x_info, y_info);
    const int input_count = static_cast<int>(x_info.shape[0]);
    const int count = std::min(input_count, max_stars);
    int neighbor_count = std::min(count, neighbors);
    neighbor_count = std::max(3, neighbor_count);
    neighbor_count = std::min(16, neighbor_count);
    const int combos = neighbor_count * (neighbor_count - 1) * (neighbor_count - 2) / 6;
    const int raw_count = count >= 3 ? count * combos : 0;
    max_count = std::max(max_count, count);
    raw_capacity = std::max(raw_capacity, raw_count);
    x_arrays.push_back(std::move(x));
    y_arrays.push_back(std::move(y));
    counts.push_back(count);
    neighbor_counts.push_back(neighbor_count);
    combos_per_frame.push_back(combos);
    raw_counts.push_back(raw_count);
  }
  const double host_prepare_s = seconds_since(host_prepare_start);

  auto empty_result_for = [&](int batch_index) {
    py::dict result;
    result["count"] = 0;
    result["raw_count"] = raw_counts[static_cast<std::size_t>(batch_index)];
    result["max_stars"] = max_stars;
    result["neighbors"] = neighbor_counts[static_cast<std::size_t>(batch_index)];
    result["descriptors"] = py::array_t<float>({0, 2});
    result["indices"] = py::array_t<int>({0, 3});
    result["areas"] = py::array_t<float>({0});
    result["model"] = "triangle_asterism_descriptors_cuda_batch_padded_one_sync";
    result["batch_index"] = batch_index;
    result["batch_count"] = static_cast<int>(batch_count_py);
    result["batch_model"] = "triangle_asterism_descriptors_cuda_batch_padded_one_sync";
    result["batch_timing_model"] = "padded_catalog_batch_one_kernel_one_sync";
    result["batch_host_prepare_s"] = host_prepare_s;
    result["batch_upload_s"] = 0.0;
    result["batch_kernel_sync_s"] = 0.0;
    result["batch_output_download_s"] = 0.0;
    result["batch_total_elapsed_s_at_result"] = seconds_since(total_start);
    return result;
  };

  if (max_count == 0 || raw_capacity == 0 || max_descriptors == 0) {
    for (py::ssize_t batch_index = 0; batch_index < batch_count_py; ++batch_index) {
      results.append(empty_result_for(static_cast<int>(batch_index)));
    }
    return results;
  }

  const std::size_t batch_count = static_cast<std::size_t>(batch_count_py);
  std::vector<float> host_x(batch_count * static_cast<std::size_t>(max_count), std::numeric_limits<float>::quiet_NaN());
  std::vector<float> host_y(batch_count * static_cast<std::size_t>(max_count), std::numeric_limits<float>::quiet_NaN());
  for (py::ssize_t batch_index = 0; batch_index < batch_count_py; ++batch_index) {
    const py::buffer_info x_info = x_arrays[static_cast<std::size_t>(batch_index)].request();
    const py::buffer_info y_info = y_arrays[static_cast<std::size_t>(batch_index)].request();
    const auto* x_ptr = static_cast<const float*>(x_info.ptr);
    const auto* y_ptr = static_cast<const float*>(y_info.ptr);
    const int count = counts[static_cast<std::size_t>(batch_index)];
    const std::size_t base = static_cast<std::size_t>(batch_index) * static_cast<std::size_t>(max_count);
    std::copy(x_ptr, x_ptr + count, host_x.begin() + static_cast<std::ptrdiff_t>(base));
    std::copy(y_ptr, y_ptr + count, host_y.begin() + static_cast<std::ptrdiff_t>(base));
  }

  const std::size_t total_raw_slots = batch_count * static_cast<std::size_t>(raw_capacity);
  std::vector<float> host_descriptors(total_raw_slots * 2, std::numeric_limits<float>::quiet_NaN());
  std::vector<int> host_indices(total_raw_slots * 3, -1);
  std::vector<float> host_areas(total_raw_slots, std::numeric_limits<float>::quiet_NaN());
  std::vector<unsigned char> host_valid(total_raw_slots, 0);

  float* d_x = nullptr;
  float* d_y = nullptr;
  float* d_descriptors = nullptr;
  int* d_indices = nullptr;
  float* d_areas = nullptr;
  unsigned char* d_valid = nullptr;
  int* d_counts = nullptr;
  int* d_neighbors = nullptr;
  int* d_combos = nullptr;
  double upload_s = 0.0;
  double kernel_sync_s = 0.0;
  double output_download_s = 0.0;
  try {
    check_cuda(cudaMalloc(&d_x, host_x.size() * sizeof(float)), "cudaMalloc(batch triangle x)");
    check_cuda(cudaMalloc(&d_y, host_y.size() * sizeof(float)), "cudaMalloc(batch triangle y)");
    check_cuda(
        cudaMalloc(&d_descriptors, host_descriptors.size() * sizeof(float)),
        "cudaMalloc(batch triangle descriptors)");
    check_cuda(
        cudaMalloc(&d_indices, host_indices.size() * sizeof(int)),
        "cudaMalloc(batch triangle indices)");
    check_cuda(cudaMalloc(&d_areas, host_areas.size() * sizeof(float)), "cudaMalloc(batch triangle areas)");
    check_cuda(cudaMalloc(&d_valid, host_valid.size() * sizeof(unsigned char)), "cudaMalloc(batch triangle valid)");
    check_cuda(cudaMalloc(&d_counts, counts.size() * sizeof(int)), "cudaMalloc(batch triangle counts)");
    check_cuda(cudaMalloc(&d_neighbors, neighbor_counts.size() * sizeof(int)), "cudaMalloc(batch triangle neighbors)");
    check_cuda(cudaMalloc(&d_combos, combos_per_frame.size() * sizeof(int)), "cudaMalloc(batch triangle combos)");
    const auto upload_start = Clock::now();
    check_cuda(cudaMemcpy(d_x, host_x.data(), host_x.size() * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(batch triangle x)");
    check_cuda(cudaMemcpy(d_y, host_y.data(), host_y.size() * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(batch triangle y)");
    check_cuda(cudaMemcpy(d_counts, counts.data(), counts.size() * sizeof(int), cudaMemcpyHostToDevice), "cudaMemcpy(batch triangle counts)");
    check_cuda(
        cudaMemcpy(
            d_neighbors,
            neighbor_counts.data(),
            neighbor_counts.size() * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle neighbors)");
    check_cuda(
        cudaMemcpy(
            d_combos,
            combos_per_frame.data(),
            combos_per_frame.size() * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle combos)");
    upload_s = seconds_since(upload_start);
    const auto kernel_sync_start = Clock::now();
    glass_triangle_asterism_descriptors_batch_f32_launch(
        d_x,
        d_y,
        d_descriptors,
        d_indices,
        d_areas,
        d_valid,
        d_counts,
        d_neighbors,
        d_combos,
        static_cast<int>(batch_count_py),
        max_count,
        raw_capacity);
    check_cuda(cudaGetLastError(), "triangle_asterism_descriptors_batch_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "triangle_asterism_descriptors_batch_f32 synchronize");
    kernel_sync_s = seconds_since(kernel_sync_start);
    const auto output_download_start = Clock::now();
    check_cuda(
        cudaMemcpy(host_descriptors.data(), d_descriptors, host_descriptors.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(batch triangle descriptors)");
    check_cuda(
        cudaMemcpy(host_indices.data(), d_indices, host_indices.size() * sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(batch triangle indices)");
    check_cuda(
        cudaMemcpy(host_areas.data(), d_areas, host_areas.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(batch triangle areas)");
    check_cuda(
        cudaMemcpy(host_valid.data(), d_valid, host_valid.size() * sizeof(unsigned char), cudaMemcpyDeviceToHost),
        "cudaMemcpy(batch triangle valid)");
    output_download_s = seconds_since(output_download_start);
  } catch (...) {
    cudaFree(d_x);
    cudaFree(d_y);
    cudaFree(d_descriptors);
    cudaFree(d_indices);
    cudaFree(d_areas);
    cudaFree(d_valid);
    cudaFree(d_counts);
    cudaFree(d_neighbors);
    cudaFree(d_combos);
    throw;
  }
  cudaFree(d_x);
  cudaFree(d_y);
  cudaFree(d_descriptors);
  cudaFree(d_indices);
  cudaFree(d_areas);
  cudaFree(d_valid);
  cudaFree(d_counts);
  cudaFree(d_neighbors);
  cudaFree(d_combos);

  struct TriangleDescriptor {
    int key0;
    int key1;
    int key2;
    float descriptor0;
    float descriptor1;
    int index0;
    int index1;
    int index2;
    float area;
  };

  for (py::ssize_t batch_index = 0; batch_index < batch_count_py; ++batch_index) {
    const int raw_count = raw_counts[static_cast<std::size_t>(batch_index)];
    if (raw_count == 0) {
      results.append(empty_result_for(static_cast<int>(batch_index)));
      continue;
    }
    const std::size_t base = static_cast<std::size_t>(batch_index) * static_cast<std::size_t>(raw_capacity);
    std::vector<TriangleDescriptor> triangles;
    triangles.reserve(static_cast<std::size_t>(raw_count));
    for (int slot = 0; slot < raw_count; ++slot) {
      const std::size_t raw_slot = base + static_cast<std::size_t>(slot);
      if (host_valid[raw_slot] == 0) {
        continue;
      }
      int index0 = host_indices[raw_slot * 3 + 0];
      int index1 = host_indices[raw_slot * 3 + 1];
      int index2 = host_indices[raw_slot * 3 + 2];
      if (index0 < 0 || index1 < 0 || index2 < 0) {
        continue;
      }
      std::array<int, 3> key{index0, index1, index2};
      std::sort(key.begin(), key.end());
      triangles.push_back(
          TriangleDescriptor{
              key[0],
              key[1],
              key[2],
              host_descriptors[raw_slot * 2 + 0],
              host_descriptors[raw_slot * 2 + 1],
              index0,
              index1,
              index2,
              host_areas[raw_slot]});
    }
    std::sort(triangles.begin(), triangles.end(), [](const TriangleDescriptor& left, const TriangleDescriptor& right) {
      if (left.key0 != right.key0) {
        return left.key0 < right.key0;
      }
      if (left.key1 != right.key1) {
        return left.key1 < right.key1;
      }
      return left.key2 < right.key2;
    });
    std::vector<TriangleDescriptor> unique_triangles;
    unique_triangles.reserve(triangles.size());
    for (const auto& triangle : triangles) {
      if (!unique_triangles.empty()) {
        const auto& previous = unique_triangles.back();
        if (previous.key0 == triangle.key0 && previous.key1 == triangle.key1 && previous.key2 == triangle.key2) {
          continue;
        }
      }
      unique_triangles.push_back(triangle);
    }
    std::sort(
        unique_triangles.begin(),
        unique_triangles.end(),
        [](const TriangleDescriptor& left, const TriangleDescriptor& right) {
          if (left.area != right.area) {
            return left.area > right.area;
          }
          if (left.key0 != right.key0) {
            return left.key0 < right.key0;
          }
          if (left.key1 != right.key1) {
            return left.key1 < right.key1;
          }
          return left.key2 < right.key2;
        });

    const int output_count =
        std::min(static_cast<int>(unique_triangles.size()), max_descriptors);
    py::array_t<float> descriptor_array({output_count, 2});
    py::array_t<int> index_array({output_count, 3});
    py::array_t<float> area_array({output_count});
    auto descriptor_info = descriptor_array.request();
    auto index_info = index_array.request();
    auto area_info = area_array.request();
    float* descriptor_ptr = static_cast<float*>(descriptor_info.ptr);
    int* index_ptr = static_cast<int*>(index_info.ptr);
    float* area_ptr = static_cast<float*>(area_info.ptr);
    for (int i = 0; i < output_count; ++i) {
      const auto& triangle = unique_triangles[static_cast<std::size_t>(i)];
      descriptor_ptr[i * 2 + 0] = triangle.descriptor0;
      descriptor_ptr[i * 2 + 1] = triangle.descriptor1;
      index_ptr[i * 3 + 0] = triangle.index0;
      index_ptr[i * 3 + 1] = triangle.index1;
      index_ptr[i * 3 + 2] = triangle.index2;
      area_ptr[i] = triangle.area;
    }

    py::dict result;
    result["count"] = output_count;
    result["raw_count"] = raw_count;
    result["max_stars"] = max_stars;
    result["neighbors"] = neighbor_counts[static_cast<std::size_t>(batch_index)];
    result["descriptors"] = descriptor_array;
    result["indices"] = index_array;
    result["areas"] = area_array;
    result["model"] = "triangle_asterism_descriptors_cuda_batch_padded_one_sync";
    result["batch_index"] = static_cast<int>(batch_index);
    result["batch_count"] = static_cast<int>(batch_count_py);
    result["batch_model"] = "triangle_asterism_descriptors_cuda_batch_padded_one_sync";
    result["batch_timing_model"] = "padded_catalog_batch_one_kernel_one_sync";
    result["batch_host_prepare_s"] = host_prepare_s;
    result["batch_upload_s"] = upload_s;
    result["batch_kernel_sync_s"] = kernel_sync_s;
    result["batch_output_download_s"] = output_download_s;
    result["batch_total_elapsed_s_at_result"] = seconds_since(total_start);
    results.append(result);
  }
  return results;
}

py::dict estimate_similarity_from_triangle_descriptors_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_descriptors,
    py::array_t<int, py::array::c_style | py::array::forcecast> reference_indices,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_descriptors,
    py::array_t<int, py::array::c_style | py::array::forcecast> moving_indices,
    float tolerance_px,
    float descriptor_radius) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  const py::buffer_info reference_descriptor_info = reference_descriptors.request();
  const py::buffer_info reference_index_info = reference_indices.request();
  const py::buffer_info moving_descriptor_info = moving_descriptors.request();
  const py::buffer_info moving_index_info = moving_indices.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(moving_x_info, moving_y_info);
  if (reference_descriptor_info.ndim != 2 || reference_descriptor_info.shape[1] != 2 ||
      moving_descriptor_info.ndim != 2 || moving_descriptor_info.shape[1] != 2) {
    throw std::invalid_argument("triangle descriptors must have shape (N, 2)");
  }
  if (reference_index_info.ndim != 2 || reference_index_info.shape[1] != 3 ||
      moving_index_info.ndim != 2 || moving_index_info.shape[1] != 3) {
    throw std::invalid_argument("triangle indices must have shape (N, 3)");
  }
  if (reference_descriptor_info.shape[0] != reference_index_info.shape[0] ||
      moving_descriptor_info.shape[0] != moving_index_info.shape[0]) {
    throw std::invalid_argument("descriptor and index row counts must match");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (descriptor_radius < 0.0f) {
    throw std::invalid_argument("descriptor_radius must be non-negative");
  }
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int moving_count = static_cast<int>(moving_x_info.shape[0]);
  const int reference_descriptor_count = static_cast<int>(reference_descriptor_info.shape[0]);
  const int moving_descriptor_count = static_cast<int>(moving_descriptor_info.shape[0]);
  if (reference_count < 3 || moving_count < 3 ||
      reference_descriptor_count == 0 || moving_descriptor_count == 0) {
    throw std::invalid_argument("triangle descriptor similarity requires at least one descriptor and three stars");
  }
  const int candidate_count = reference_descriptor_count * moving_descriptor_count * 2;

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_reference_descriptors = nullptr;
  int* d_reference_indices = nullptr;
  float* d_moving_descriptors = nullptr;
  int* d_moving_indices = nullptr;
  float* d_candidate_params = nullptr;
  int* d_candidate_scores = nullptr;
  float* d_candidate_rms = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_best_inliers = nullptr;
  int* d_best_index = nullptr;
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int best_inliers = 0;
  int best_index = -1;
  try {
    check_cuda(cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)), "cudaMalloc(triangle similarity reference x)");
    check_cuda(cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)), "cudaMalloc(triangle similarity reference y)");
    check_cuda(cudaMalloc(&d_moving_x, static_cast<std::size_t>(moving_count) * sizeof(float)), "cudaMalloc(triangle similarity moving x)");
    check_cuda(cudaMalloc(&d_moving_y, static_cast<std::size_t>(moving_count) * sizeof(float)), "cudaMalloc(triangle similarity moving y)");
    check_cuda(
        cudaMalloc(&d_reference_descriptors, static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float)),
        "cudaMalloc(triangle similarity reference descriptors)");
    check_cuda(
        cudaMalloc(&d_reference_indices, static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int)),
        "cudaMalloc(triangle similarity reference indices)");
    check_cuda(
        cudaMalloc(&d_moving_descriptors, static_cast<std::size_t>(moving_descriptor_count) * 2 * sizeof(float)),
        "cudaMalloc(triangle similarity moving descriptors)");
    check_cuda(
        cudaMalloc(&d_moving_indices, static_cast<std::size_t>(moving_descriptor_count) * 3 * sizeof(int)),
        "cudaMalloc(triangle similarity moving indices)");
    check_cuda(
        cudaMalloc(&d_candidate_params, static_cast<std::size_t>(candidate_count) * 4 * sizeof(float)),
        "cudaMalloc(triangle similarity candidate params)");
    check_cuda(
        cudaMalloc(&d_candidate_scores, static_cast<std::size_t>(candidate_count) * sizeof(int)),
        "cudaMalloc(triangle similarity candidate scores)");
    check_cuda(
        cudaMalloc(&d_candidate_rms, static_cast<std::size_t>(candidate_count) * sizeof(float)),
        "cudaMalloc(triangle similarity candidate rms)");
    check_cuda(cudaMalloc(&d_matrix, host_matrix.size() * sizeof(float)), "cudaMalloc(triangle similarity matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(triangle similarity scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(triangle similarity rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(triangle similarity rms)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(triangle similarity best inliers)");
    check_cuda(cudaMalloc(&d_best_index, sizeof(int)), "cudaMalloc(triangle similarity best index)");
    check_cuda(
        cudaMemcpy(d_reference_x, reference_x_info.ptr, static_cast<std::size_t>(reference_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference x)");
    check_cuda(
        cudaMemcpy(d_reference_y, reference_y_info.ptr, static_cast<std::size_t>(reference_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference y)");
    check_cuda(
        cudaMemcpy(d_moving_x, moving_x_info.ptr, static_cast<std::size_t>(moving_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving x)");
    check_cuda(
        cudaMemcpy(d_moving_y, moving_y_info.ptr, static_cast<std::size_t>(moving_count) * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving y)");
    check_cuda(
        cudaMemcpy(
            d_reference_descriptors,
            reference_descriptor_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference descriptors)");
    check_cuda(
        cudaMemcpy(
            d_reference_indices,
            reference_index_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity reference indices)");
    check_cuda(
        cudaMemcpy(
            d_moving_descriptors,
            moving_descriptor_info.ptr,
            static_cast<std::size_t>(moving_descriptor_count) * 2 * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving descriptors)");
    check_cuda(
        cudaMemcpy(
            d_moving_indices,
            moving_index_info.ptr,
            static_cast<std::size_t>(moving_descriptor_count) * 3 * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(triangle similarity moving indices)");
    glass_estimate_similarity_from_triangle_descriptors_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_reference_descriptors,
        d_reference_indices,
        d_moving_descriptors,
        d_moving_indices,
        d_candidate_params,
        d_candidate_scores,
        d_candidate_rms,
        d_matrix,
        d_scale,
        d_rotation_rad,
        d_rms_px,
        d_best_inliers,
        d_best_index,
        reference_count,
        moving_count,
        reference_descriptor_count,
        moving_descriptor_count,
        candidate_count,
        tolerance_px,
        descriptor_radius);
    check_cuda(cudaGetLastError(), "estimate_similarity_from_triangle_descriptors_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_triangle_descriptors_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle similarity matrix)");
    check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(triangle similarity scale)");
    check_cuda(
        cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle similarity rotation)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(triangle similarity rms)");
    check_cuda(
        cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(triangle similarity best inliers)");
    check_cuda(cudaMemcpy(&best_index, d_best_index, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(triangle similarity best index)");
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_reference_descriptors);
    cudaFree(d_reference_indices);
    cudaFree(d_moving_descriptors);
    cudaFree(d_moving_indices);
    cudaFree(d_candidate_params);
    cudaFree(d_candidate_scores);
    cudaFree(d_candidate_rms);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_best_inliers);
    cudaFree(d_best_index);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_reference_descriptors);
  cudaFree(d_reference_indices);
  cudaFree(d_moving_descriptors);
  cudaFree(d_moving_indices);
  cudaFree(d_candidate_params);
  cudaFree(d_candidate_scores);
  cudaFree(d_candidate_rms);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_best_inliers);
  cudaFree(d_best_index);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list matrix_row;
    for (int col = 0; col < 3; ++col) {
      matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(matrix_row);
  }
  py::dict result;
  result["matrix"] = matrix_rows;
  result["scale"] = scale;
  result["rotation_rad"] = rotation_rad;
  result["rms_px"] = rms_px;
  result["inliers"] = best_inliers;
  result["best_candidate_index"] = best_index;
  result["candidate_count"] = candidate_count;
  result["reference_count"] = reference_count;
  result["moving_count"] = moving_count;
  result["reference_descriptor_count"] = reference_descriptor_count;
  result["moving_descriptor_count"] = moving_descriptor_count;
  result["tolerance_px"] = tolerance_px;
  result["descriptor_radius"] = descriptor_radius;
  result["status"] = best_inliers > 0 ? "ok" : "failed";
  result["model"] = "triangle_descriptor_similarity_cuda";
  result["best_reduction_mode"] = "single_block_parallel_score_rms_index";
  return result;
}

py::list estimate_similarity_from_triangle_descriptors_batch_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_descriptors,
    py::array_t<int, py::array::c_style | py::array::forcecast> reference_indices,
    py::sequence moving_x_list,
    py::sequence moving_y_list,
    py::sequence moving_descriptors_list,
    py::sequence moving_indices_list,
    float tolerance_px,
    float descriptor_radius) {
  const auto batch_total_start = Clock::now();
  const py::ssize_t batch_count = py::len(moving_x_list);
  if (static_cast<py::ssize_t>(py::len(moving_y_list)) != batch_count ||
      static_cast<py::ssize_t>(py::len(moving_descriptors_list)) != batch_count ||
      static_cast<py::ssize_t>(py::len(moving_indices_list)) != batch_count) {
    throw std::invalid_argument("moving batch lists must have the same length");
  }
  py::list results;
  if (batch_count == 0) {
    return results;
  }
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info reference_descriptor_info = reference_descriptors.request();
  const py::buffer_info reference_index_info = reference_indices.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1) {
    throw std::invalid_argument("reference catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  if (reference_descriptor_info.ndim != 2 || reference_descriptor_info.shape[1] != 2) {
    throw std::invalid_argument("reference triangle descriptors must have shape (N, 2)");
  }
  if (reference_index_info.ndim != 2 || reference_index_info.shape[1] != 3) {
    throw std::invalid_argument("reference triangle indices must have shape (N, 3)");
  }
  if (reference_descriptor_info.shape[0] != reference_index_info.shape[0]) {
    throw std::invalid_argument("reference descriptor and index row counts must match");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (descriptor_radius < 0.0f) {
    throw std::invalid_argument("descriptor_radius must be non-negative");
  }
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int reference_descriptor_count = static_cast<int>(reference_descriptor_info.shape[0]);
  if (reference_count < 3 || reference_descriptor_count == 0) {
    throw std::invalid_argument("triangle descriptor batch similarity requires reference descriptors and three stars");
  }
  const std::size_t reference_device_bytes =
      static_cast<std::size_t>(reference_count) * 2 * sizeof(float) +
      static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float) +
      static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int);

  using FloatArray = py::array_t<float, py::array::c_style | py::array::forcecast>;
  using IntArray = py::array_t<int, py::array::c_style | py::array::forcecast>;
  const auto host_prepare_start = Clock::now();
  std::vector<FloatArray> moving_x_arrays;
  std::vector<FloatArray> moving_y_arrays;
  std::vector<FloatArray> moving_descriptor_arrays;
  std::vector<IntArray> moving_index_arrays;
  moving_x_arrays.reserve(static_cast<std::size_t>(batch_count));
  moving_y_arrays.reserve(static_cast<std::size_t>(batch_count));
  moving_descriptor_arrays.reserve(static_cast<std::size_t>(batch_count));
  moving_index_arrays.reserve(static_cast<std::size_t>(batch_count));
  std::size_t max_moving_count = 0;
  std::size_t max_moving_descriptor_count = 0;
  std::size_t max_candidate_count = 0;
  for (py::ssize_t batch_index = 0; batch_index < batch_count; ++batch_index) {
    auto moving_x = FloatArray::ensure(moving_x_list[batch_index]);
    auto moving_y = FloatArray::ensure(moving_y_list[batch_index]);
    auto moving_descriptors = FloatArray::ensure(moving_descriptors_list[batch_index]);
    auto moving_indices = IntArray::ensure(moving_indices_list[batch_index]);
    if (!moving_x || !moving_y || !moving_descriptors || !moving_indices) {
      throw std::invalid_argument("moving batch items must be convertible to arrays");
    }
    const py::buffer_info moving_x_info = moving_x.request();
    const py::buffer_info moving_y_info = moving_y.request();
    const py::buffer_info moving_descriptor_info = moving_descriptors.request();
    const py::buffer_info moving_index_info = moving_indices.request();
    if (moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
      throw std::invalid_argument("moving catalog coordinate arrays must be one-dimensional");
    }
    require_same_shape(moving_x_info, moving_y_info);
    if (moving_descriptor_info.ndim != 2 || moving_descriptor_info.shape[1] != 2) {
      throw std::invalid_argument("moving triangle descriptors must have shape (N, 2)");
    }
    if (moving_index_info.ndim != 2 || moving_index_info.shape[1] != 3) {
      throw std::invalid_argument("moving triangle indices must have shape (N, 3)");
    }
    if (moving_descriptor_info.shape[0] != moving_index_info.shape[0]) {
      throw std::invalid_argument("moving descriptor and index row counts must match");
    }
    const int moving_count = static_cast<int>(moving_x_info.shape[0]);
    const int moving_descriptor_count = static_cast<int>(moving_descriptor_info.shape[0]);
    if (moving_count < 3 || moving_descriptor_count == 0) {
      throw std::invalid_argument("triangle descriptor batch similarity requires moving descriptors and three stars");
    }
    max_moving_count = std::max(max_moving_count, static_cast<std::size_t>(moving_count));
    max_moving_descriptor_count =
        std::max(max_moving_descriptor_count, static_cast<std::size_t>(moving_descriptor_count));
    max_candidate_count = std::max(
        max_candidate_count,
        static_cast<std::size_t>(reference_descriptor_count) *
            static_cast<std::size_t>(moving_descriptor_count) * 2);
    moving_x_arrays.push_back(std::move(moving_x));
    moving_y_arrays.push_back(std::move(moving_y));
    moving_descriptor_arrays.push_back(std::move(moving_descriptors));
    moving_index_arrays.push_back(std::move(moving_indices));
  }
  const double host_prepare_s = seconds_since(host_prepare_start);
  const std::size_t moving_device_bytes =
      max_moving_count * 2 * sizeof(float) +
      max_moving_descriptor_count * 2 * sizeof(float) +
      max_moving_descriptor_count * 3 * sizeof(int);
  const std::size_t output_device_bytes =
      max_candidate_count * 4 * sizeof(float) +
      max_candidate_count * sizeof(int) +
      max_candidate_count * sizeof(float) +
      9 * sizeof(float) +
      sizeof(float) * 3 +
      sizeof(int) * 2;

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_reference_descriptors = nullptr;
  int* d_reference_indices = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_moving_descriptors = nullptr;
  int* d_moving_indices = nullptr;
  float* d_candidate_params = nullptr;
  int* d_candidate_scores = nullptr;
  float* d_candidate_rms = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_best_inliers = nullptr;
  int* d_best_index = nullptr;
  double reference_alloc_s = 0.0;
  double reference_upload_s = 0.0;
  double workspace_alloc_s = 0.0;
  try {
    const auto reference_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(batch triangle similarity reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(batch triangle similarity reference y)");
    check_cuda(
        cudaMalloc(
            &d_reference_descriptors,
            static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float)),
        "cudaMalloc(batch triangle similarity reference descriptors)");
    check_cuda(
        cudaMalloc(
            &d_reference_indices,
            static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int)),
        "cudaMalloc(batch triangle similarity reference indices)");
    reference_alloc_s = seconds_since(reference_alloc_start);
    const auto reference_upload_start = Clock::now();
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference y)");
    check_cuda(
        cudaMemcpy(
            d_reference_descriptors,
            reference_descriptor_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 2 * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference descriptors)");
    check_cuda(
        cudaMemcpy(
            d_reference_indices,
            reference_index_info.ptr,
            static_cast<std::size_t>(reference_descriptor_count) * 3 * sizeof(int),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(batch triangle similarity reference indices)");
    reference_upload_s = seconds_since(reference_upload_start);
    const auto workspace_alloc_start = Clock::now();
    check_cuda(
        cudaMalloc(&d_moving_x, max_moving_count * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, max_moving_count * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable moving y)");
    check_cuda(
        cudaMalloc(&d_moving_descriptors, max_moving_descriptor_count * 2 * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable moving descriptors)");
    check_cuda(
        cudaMalloc(&d_moving_indices, max_moving_descriptor_count * 3 * sizeof(int)),
        "cudaMalloc(batch triangle similarity reusable moving indices)");
    check_cuda(
        cudaMalloc(&d_candidate_params, max_candidate_count * 4 * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable candidate params)");
    check_cuda(
        cudaMalloc(&d_candidate_scores, max_candidate_count * sizeof(int)),
        "cudaMalloc(batch triangle similarity reusable candidate scores)");
    check_cuda(
        cudaMalloc(&d_candidate_rms, max_candidate_count * sizeof(float)),
        "cudaMalloc(batch triangle similarity reusable candidate rms)");
    check_cuda(cudaMalloc(&d_matrix, 9 * sizeof(float)), "cudaMalloc(batch triangle similarity reusable matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(batch triangle similarity reusable scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(batch triangle similarity reusable rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(batch triangle similarity reusable rms)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(batch triangle similarity reusable best inliers)");
    check_cuda(cudaMalloc(&d_best_index, sizeof(int)), "cudaMalloc(batch triangle similarity reusable best index)");
    workspace_alloc_s = seconds_since(workspace_alloc_start);

  for (py::ssize_t batch_index = 0; batch_index < batch_count; ++batch_index) {
    const auto frame_total_start = Clock::now();
    const auto& moving_x = moving_x_arrays[static_cast<std::size_t>(batch_index)];
    const auto& moving_y = moving_y_arrays[static_cast<std::size_t>(batch_index)];
    const auto& moving_descriptors = moving_descriptor_arrays[static_cast<std::size_t>(batch_index)];
    const auto& moving_indices = moving_index_arrays[static_cast<std::size_t>(batch_index)];
    const py::buffer_info moving_x_info = moving_x.request();
    const py::buffer_info moving_y_info = moving_y.request();
    const py::buffer_info moving_descriptor_info = moving_descriptors.request();
    const py::buffer_info moving_index_info = moving_indices.request();
    const int moving_count = static_cast<int>(moving_x_info.shape[0]);
    const int moving_descriptor_count = static_cast<int>(moving_descriptor_info.shape[0]);
    const int candidate_count = reference_descriptor_count * moving_descriptor_count * 2;

    std::array<float, 9> host_matrix{};
    float scale = 1.0f;
    float rotation_rad = 0.0f;
    float rms_px = std::numeric_limits<float>::quiet_NaN();
    int best_inliers = 0;
    int best_index = -1;
      const auto moving_upload_start = Clock::now();
      check_cuda(
          cudaMemcpy(
              d_moving_x,
              moving_x_info.ptr,
              static_cast<std::size_t>(moving_count) * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving x)");
      check_cuda(
          cudaMemcpy(
              d_moving_y,
              moving_y_info.ptr,
              static_cast<std::size_t>(moving_count) * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving y)");
      check_cuda(
          cudaMemcpy(
              d_moving_descriptors,
              moving_descriptor_info.ptr,
              static_cast<std::size_t>(moving_descriptor_count) * 2 * sizeof(float),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving descriptors)");
      check_cuda(
          cudaMemcpy(
              d_moving_indices,
              moving_index_info.ptr,
              static_cast<std::size_t>(moving_descriptor_count) * 3 * sizeof(int),
              cudaMemcpyHostToDevice),
          "cudaMemcpy(batch triangle similarity moving indices)");
      const double moving_upload_s = seconds_since(moving_upload_start);
      const auto kernel_sync_start = Clock::now();
      glass_estimate_similarity_from_triangle_descriptors_f32_launch(
          d_reference_x,
          d_reference_y,
          d_moving_x,
          d_moving_y,
          d_reference_descriptors,
          d_reference_indices,
          d_moving_descriptors,
          d_moving_indices,
          d_candidate_params,
          d_candidate_scores,
          d_candidate_rms,
          d_matrix,
          d_scale,
          d_rotation_rad,
          d_rms_px,
          d_best_inliers,
          d_best_index,
          reference_count,
          moving_count,
          reference_descriptor_count,
          moving_descriptor_count,
          candidate_count,
          tolerance_px,
          descriptor_radius);
      check_cuda(cudaGetLastError(), "estimate_similarity_from_triangle_descriptors_batch_f32 kernel launch");
      check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_triangle_descriptors_batch_f32 synchronize");
      const double kernel_sync_s = seconds_since(kernel_sync_start);
      const auto output_download_start = Clock::now();
      check_cuda(
          cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(batch triangle similarity matrix)");
      check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(batch triangle similarity scale)");
      check_cuda(
          cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
          "cudaMemcpy(batch triangle similarity rotation)");
      check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(batch triangle similarity rms)");
      check_cuda(
          cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
          "cudaMemcpy(batch triangle similarity best inliers)");
      check_cuda(cudaMemcpy(&best_index, d_best_index, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(batch triangle similarity best index)");
      const double output_download_s = seconds_since(output_download_start);
      const double frame_total_s = seconds_since(frame_total_start);

    py::list matrix_rows;
    for (int row = 0; row < 3; ++row) {
      py::list matrix_row;
      for (int col = 0; col < 3; ++col) {
        matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
      }
      matrix_rows.append(matrix_row);
    }
    py::dict result;
    result["matrix"] = matrix_rows;
    result["scale"] = scale;
    result["rotation_rad"] = rotation_rad;
    result["rms_px"] = rms_px;
    result["inliers"] = best_inliers;
    result["best_candidate_index"] = best_index;
    result["candidate_count"] = candidate_count;
    result["reference_count"] = reference_count;
    result["moving_count"] = moving_count;
    result["reference_descriptor_count"] = reference_descriptor_count;
    result["moving_descriptor_count"] = moving_descriptor_count;
    result["tolerance_px"] = tolerance_px;
    result["descriptor_radius"] = descriptor_radius;
    result["status"] = best_inliers > 0 ? "ok" : "failed";
    result["model"] = "triangle_descriptor_similarity_cuda";
    result["best_reduction_mode"] = "single_block_parallel_score_rms_index";
    result["batch_index"] = static_cast<int>(batch_index);
    result["batch_count"] = static_cast<int>(batch_count);
    result["batch_model"] = "triangle_descriptor_similarity_cuda_batch_shared_reference_device";
    result["reference_device_reuse"] = true;
    result["reference_device_bytes"] = static_cast<unsigned long long>(reference_device_bytes);
    result["moving_device_reuse"] = true;
    result["moving_device_bytes"] = static_cast<unsigned long long>(moving_device_bytes);
    result["output_device_reuse"] = true;
    result["output_device_bytes"] = static_cast<unsigned long long>(output_device_bytes);
    result["batch_timing_model"] = "per_frame_reused_buffers_sync_timed";
    result["batch_host_prepare_s"] = host_prepare_s;
    result["batch_reference_alloc_s"] = reference_alloc_s;
    result["batch_reference_upload_s"] = reference_upload_s;
    result["batch_workspace_alloc_s"] = workspace_alloc_s;
    result["batch_frame_moving_upload_s"] = moving_upload_s;
    result["batch_frame_kernel_sync_s"] = kernel_sync_s;
    result["batch_frame_output_download_s"] = output_download_s;
    result["batch_frame_total_s"] = frame_total_s;
    result["batch_total_elapsed_s_at_result"] = seconds_since(batch_total_start);
    results.append(result);
  }
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_reference_descriptors);
    cudaFree(d_reference_indices);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_moving_descriptors);
    cudaFree(d_moving_indices);
    cudaFree(d_candidate_params);
    cudaFree(d_candidate_scores);
    cudaFree(d_candidate_rms);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_best_inliers);
    cudaFree(d_best_index);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_reference_descriptors);
  cudaFree(d_reference_indices);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_moving_descriptors);
  cudaFree(d_moving_indices);
  cudaFree(d_candidate_params);
  cudaFree(d_candidate_scores);
  cudaFree(d_candidate_rms);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_best_inliers);
  cudaFree(d_best_index);
  return results;
}

py::dict estimate_similarity_from_catalogs_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference_y,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_x,
    py::array_t<float, py::array::c_style | py::array::forcecast> moving_y,
    float tolerance_px,
    float min_pair_distance,
    float prior_dx,
    float prior_dy,
    float prior_radius_px,
    float min_scale,
    float max_scale,
    float max_abs_rotation_rad,
    int top_k) {
  const py::buffer_info reference_x_info = reference_x.request();
  const py::buffer_info reference_y_info = reference_y.request();
  const py::buffer_info moving_x_info = moving_x.request();
  const py::buffer_info moving_y_info = moving_y.request();
  if (reference_x_info.ndim != 1 || reference_y_info.ndim != 1 ||
      moving_x_info.ndim != 1 || moving_y_info.ndim != 1) {
    throw std::invalid_argument("catalog coordinate arrays must be one-dimensional");
  }
  require_same_shape(reference_x_info, reference_y_info);
  require_same_shape(moving_x_info, moving_y_info);
  const int reference_count = static_cast<int>(reference_x_info.shape[0]);
  const int moving_count = static_cast<int>(moving_x_info.shape[0]);
  if (reference_count < 2 || moving_count < 2) {
    throw std::invalid_argument("similarity catalog estimation requires at least two stars per catalog");
  }
  if (tolerance_px < 0.0f) {
    throw std::invalid_argument("tolerance_px must be non-negative");
  }
  if (min_pair_distance < 0.0f) {
    throw std::invalid_argument("min_pair_distance must be non-negative");
  }
  if (prior_radius_px < 0.0f) {
    prior_dx = 0.0f;
    prior_dy = 0.0f;
  }
  if (min_scale < 0.0f || max_scale < min_scale) {
    throw std::invalid_argument("scale constraints must satisfy 0 <= min_scale <= max_scale");
  }
  if (max_abs_rotation_rad < 0.0f) {
    max_abs_rotation_rad = -1.0f;
  }
  if (top_k < 0) {
    throw std::invalid_argument("top_k must be non-negative");
  }
  const int candidate_count =
      reference_count * (reference_count - 1) * moving_count * (moving_count - 1);

  float* d_reference_x = nullptr;
  float* d_reference_y = nullptr;
  float* d_moving_x = nullptr;
  float* d_moving_y = nullptr;
  float* d_candidate_params = nullptr;
  int* d_candidate_scores = nullptr;
  float* d_candidate_rms = nullptr;
  float* d_matrix = nullptr;
  float* d_scale = nullptr;
  float* d_rotation_rad = nullptr;
  float* d_rms_px = nullptr;
  int* d_best_inliers = nullptr;
  int* d_best_index = nullptr;
  int* d_refit_inliers = nullptr;
  int* d_refit_status = nullptr;
  float* d_refit_matrix = nullptr;
  float* d_refit_scale = nullptr;
  float* d_refit_rotation_rad = nullptr;
  float* d_refit_rms_px = nullptr;
  double* d_refit_partial_sums = nullptr;
  unsigned long long* d_refit_partial_count = nullptr;
  double* d_refit_partial_residual_sums = nullptr;
  std::array<float, 9> host_matrix{};
  float scale = 1.0f;
  float rotation_rad = 0.0f;
  float rms_px = std::numeric_limits<float>::quiet_NaN();
  int best_inliers = 0;
  int best_index = -1;
  int refit_inliers = 0;
  int refit_status = 0;
  float refit_rms_px = std::numeric_limits<float>::quiet_NaN();
  py::list top_candidates;
  constexpr int refit_threads = 256;
  const int refit_blocks = std::max(1, (moving_count + refit_threads - 1) / refit_threads);
  try {
    check_cuda(
        cudaMalloc(&d_reference_x, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(similarity catalog reference x)");
    check_cuda(
        cudaMalloc(&d_reference_y, static_cast<std::size_t>(reference_count) * sizeof(float)),
        "cudaMalloc(similarity catalog reference y)");
    check_cuda(
        cudaMalloc(&d_moving_x, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(similarity catalog moving x)");
    check_cuda(
        cudaMalloc(&d_moving_y, static_cast<std::size_t>(moving_count) * sizeof(float)),
        "cudaMalloc(similarity catalog moving y)");
    check_cuda(
        cudaMalloc(&d_candidate_params, static_cast<std::size_t>(candidate_count) * 4 * sizeof(float)),
        "cudaMalloc(similarity catalog candidate params)");
    check_cuda(
        cudaMalloc(&d_candidate_scores, static_cast<std::size_t>(candidate_count) * sizeof(int)),
        "cudaMalloc(similarity catalog candidate scores)");
    check_cuda(
        cudaMalloc(&d_candidate_rms, static_cast<std::size_t>(candidate_count) * sizeof(float)),
        "cudaMalloc(similarity catalog candidate rms)");
    check_cuda(cudaMalloc(&d_matrix, host_matrix.size() * sizeof(float)), "cudaMalloc(similarity catalog matrix)");
    check_cuda(cudaMalloc(&d_scale, sizeof(float)), "cudaMalloc(similarity catalog scale)");
    check_cuda(cudaMalloc(&d_rotation_rad, sizeof(float)), "cudaMalloc(similarity catalog rotation)");
    check_cuda(cudaMalloc(&d_rms_px, sizeof(float)), "cudaMalloc(similarity catalog rms)");
    check_cuda(cudaMalloc(&d_best_inliers, sizeof(int)), "cudaMalloc(similarity catalog best inliers)");
    check_cuda(cudaMalloc(&d_best_index, sizeof(int)), "cudaMalloc(similarity catalog best index)");
    check_cuda(cudaMalloc(&d_refit_inliers, sizeof(int)), "cudaMalloc(similarity catalog refit inliers)");
    check_cuda(cudaMalloc(&d_refit_status, sizeof(int)), "cudaMalloc(similarity catalog refit status)");
    check_cuda(
        cudaMalloc(&d_refit_matrix, host_matrix.size() * sizeof(float)),
        "cudaMalloc(similarity catalog refit matrix)");
    check_cuda(cudaMalloc(&d_refit_scale, sizeof(float)), "cudaMalloc(similarity catalog refit scale)");
    check_cuda(
        cudaMalloc(&d_refit_rotation_rad, sizeof(float)),
        "cudaMalloc(similarity catalog refit rotation)");
    check_cuda(cudaMalloc(&d_refit_rms_px, sizeof(float)), "cudaMalloc(similarity catalog refit rms)");
    check_cuda(
        cudaMalloc(&d_refit_partial_sums, static_cast<std::size_t>(refit_blocks) * 7 * sizeof(double)),
        "cudaMalloc(similarity catalog refit partial sums)");
    check_cuda(
        cudaMalloc(
            &d_refit_partial_count,
            static_cast<std::size_t>(refit_blocks) * sizeof(unsigned long long)),
        "cudaMalloc(similarity catalog refit partial count)");
    check_cuda(
        cudaMalloc(
            &d_refit_partial_residual_sums,
            static_cast<std::size_t>(refit_blocks) * sizeof(double)),
        "cudaMalloc(similarity catalog refit partial residual sums)");
    check_cuda(
        cudaMemcpy(
            d_reference_x,
            reference_x_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog reference x)");
    check_cuda(
        cudaMemcpy(
            d_reference_y,
            reference_y_info.ptr,
            static_cast<std::size_t>(reference_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog reference y)");
    check_cuda(
        cudaMemcpy(
            d_moving_x,
            moving_x_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog moving x)");
    check_cuda(
        cudaMemcpy(
            d_moving_y,
            moving_y_info.ptr,
            static_cast<std::size_t>(moving_count) * sizeof(float),
            cudaMemcpyHostToDevice),
        "cudaMemcpy(similarity catalog moving y)");
    glass_estimate_similarity_from_catalogs_f32_launch(
        d_reference_x,
        d_reference_y,
        d_moving_x,
        d_moving_y,
        d_candidate_params,
        d_candidate_scores,
        d_candidate_rms,
        d_matrix,
        d_scale,
        d_rotation_rad,
        d_rms_px,
        d_best_inliers,
        d_best_index,
        d_refit_inliers,
        d_refit_status,
        d_refit_matrix,
        d_refit_scale,
        d_refit_rotation_rad,
        d_refit_rms_px,
        d_refit_partial_sums,
        d_refit_partial_count,
        d_refit_partial_residual_sums,
        refit_blocks,
        reference_count,
        moving_count,
        candidate_count,
        tolerance_px,
        min_pair_distance,
        prior_dx,
        prior_dy,
        prior_radius_px,
        min_scale,
        max_scale,
        max_abs_rotation_rad);
    check_cuda(cudaGetLastError(), "estimate_similarity_from_catalogs_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "estimate_similarity_from_catalogs_f32 synchronize");
    check_cuda(
        cudaMemcpy(host_matrix.data(), d_matrix, host_matrix.size() * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog matrix)");
    check_cuda(cudaMemcpy(&scale, d_scale, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity catalog scale)");
    check_cuda(
        cudaMemcpy(&rotation_rad, d_rotation_rad, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog rotation)");
    check_cuda(cudaMemcpy(&rms_px, d_rms_px, sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity catalog rms)");
    check_cuda(
        cudaMemcpy(&best_inliers, d_best_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog best inliers)");
    check_cuda(cudaMemcpy(&best_index, d_best_index, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(similarity catalog best index)");
    check_cuda(
        cudaMemcpy(&refit_inliers, d_refit_inliers, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog refit inliers)");
    check_cuda(
        cudaMemcpy(&refit_status, d_refit_status, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog refit status)");
    check_cuda(
        cudaMemcpy(&refit_rms_px, d_refit_rms_px, sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(similarity catalog refit rms)");
    if (top_k > 0) {
      std::vector<float> candidate_params(static_cast<std::size_t>(candidate_count) * 4, 0.0f);
      std::vector<int> candidate_scores(static_cast<std::size_t>(candidate_count), -1);
      std::vector<float> candidate_rms(static_cast<std::size_t>(candidate_count), std::numeric_limits<float>::quiet_NaN());
      check_cuda(
          cudaMemcpy(
              candidate_params.data(),
              d_candidate_params,
              candidate_params.size() * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(similarity catalog candidate params)");
      check_cuda(
          cudaMemcpy(
              candidate_scores.data(),
              d_candidate_scores,
              candidate_scores.size() * sizeof(int),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(similarity catalog candidate scores)");
      check_cuda(
          cudaMemcpy(
              candidate_rms.data(),
              d_candidate_rms,
              candidate_rms.size() * sizeof(float),
              cudaMemcpyDeviceToHost),
          "cudaMemcpy(similarity catalog candidate rms)");
      const int per_score_limit = std::max(1, (top_k + 3) / 4);
      const int score_bucket_count = std::max(reference_count, moving_count) + 1;
      std::vector<std::vector<int>> per_score_best(static_cast<std::size_t>(score_bucket_count));
      std::vector<int> global_best;
      global_best.reserve(static_cast<std::size_t>(std::min(top_k, candidate_count)));
      auto insert_limited = [&](std::vector<int>& selected, int candidate_index, int limit) {
        if (limit <= 0) {
          return;
        }
        if (static_cast<int>(selected.size()) < limit) {
          selected.push_back(candidate_index);
        } else {
          int worst_pos = 0;
          for (int pos = 1; pos < static_cast<int>(selected.size()); ++pos) {
            const int current = selected[static_cast<std::size_t>(pos)];
            const int worst = selected[static_cast<std::size_t>(worst_pos)];
            const int current_score = candidate_scores[static_cast<std::size_t>(current)];
            const int worst_score = candidate_scores[static_cast<std::size_t>(worst)];
            const float current_rms = candidate_rms[static_cast<std::size_t>(current)];
            const float worst_rms = candidate_rms[static_cast<std::size_t>(worst)];
            if (current_score < worst_score ||
                (current_score == worst_score && current_rms > worst_rms)) {
              worst_pos = pos;
            }
          }
          const int worst = selected[static_cast<std::size_t>(worst_pos)];
          const int worst_score = candidate_scores[static_cast<std::size_t>(worst)];
          const float worst_rms = candidate_rms[static_cast<std::size_t>(worst)];
          const int score = candidate_scores[static_cast<std::size_t>(candidate_index)];
          const float rms = candidate_rms[static_cast<std::size_t>(candidate_index)];
          if (score > worst_score || (score == worst_score && rms < worst_rms)) {
            selected[static_cast<std::size_t>(worst_pos)] = candidate_index;
          }
        }
      };
      for (int i = 0; i < candidate_count; ++i) {
        const int score = candidate_scores[static_cast<std::size_t>(i)];
        const float rms = candidate_rms[static_cast<std::size_t>(i)];
        if (score < 0 || !std::isfinite(rms)) {
          continue;
        }
        insert_limited(global_best, i, top_k);
        if (score < score_bucket_count) {
          insert_limited(per_score_best[static_cast<std::size_t>(score)], i, per_score_limit);
        }
      }
      std::vector<int> selected;
      selected.reserve(static_cast<std::size_t>(std::min(top_k, candidate_count)));
      for (int score = score_bucket_count - 1; score >= 0 && static_cast<int>(selected.size()) < top_k; --score) {
        auto& bucket = per_score_best[static_cast<std::size_t>(score)];
        std::sort(bucket.begin(), bucket.end(), [&](int left, int right) {
          const float left_rms = candidate_rms[static_cast<std::size_t>(left)];
          const float right_rms = candidate_rms[static_cast<std::size_t>(right)];
          if (left_rms != right_rms) {
            return left_rms < right_rms;
          }
          return left < right;
        });
        for (const int candidate_index : bucket) {
          if (static_cast<int>(selected.size()) >= top_k) {
            break;
          }
          if (std::find(selected.begin(), selected.end(), candidate_index) == selected.end()) {
            selected.push_back(candidate_index);
          }
        }
      }
      for (const int candidate_index : global_best) {
        if (static_cast<int>(selected.size()) >= top_k) {
          break;
        }
        if (std::find(selected.begin(), selected.end(), candidate_index) == selected.end()) {
          selected.push_back(candidate_index);
        }
      }
      std::sort(selected.begin(), selected.end(), [&](int left, int right) {
        const int left_score = candidate_scores[static_cast<std::size_t>(left)];
        const int right_score = candidate_scores[static_cast<std::size_t>(right)];
        if (left_score != right_score) {
          return left_score > right_score;
        }
        const float left_rms = candidate_rms[static_cast<std::size_t>(left)];
        const float right_rms = candidate_rms[static_cast<std::size_t>(right)];
        if (left_rms != right_rms) {
          return left_rms < right_rms;
        }
        return left < right;
      });
      for (const int candidate_index : selected) {
        const std::size_t param_offset = static_cast<std::size_t>(candidate_index) * 4;
        const float a = candidate_params[param_offset + 0];
        const float b = candidate_params[param_offset + 1];
        const float tx = candidate_params[param_offset + 2];
        const float ty = candidate_params[param_offset + 3];
        py::list matrix_rows_candidate;
        py::list row0;
        row0.append(a);
        row0.append(-b);
        row0.append(tx);
        py::list row1;
        row1.append(b);
        row1.append(a);
        row1.append(ty);
        py::list row2;
        row2.append(0.0f);
        row2.append(0.0f);
        row2.append(1.0f);
        matrix_rows_candidate.append(row0);
        matrix_rows_candidate.append(row1);
        matrix_rows_candidate.append(row2);
        py::dict candidate;
        candidate["candidate_index"] = candidate_index;
        candidate["inliers"] = candidate_scores[static_cast<std::size_t>(candidate_index)];
        candidate["rms_px"] = candidate_rms[static_cast<std::size_t>(candidate_index)];
        candidate["matrix"] = matrix_rows_candidate;
        candidate["scale"] = std::sqrt(a * a + b * b);
        candidate["rotation_rad"] = std::atan2(b, a);
        top_candidates.append(candidate);
      }
    }
  } catch (...) {
    cudaFree(d_reference_x);
    cudaFree(d_reference_y);
    cudaFree(d_moving_x);
    cudaFree(d_moving_y);
    cudaFree(d_candidate_params);
    cudaFree(d_candidate_scores);
    cudaFree(d_candidate_rms);
    cudaFree(d_matrix);
    cudaFree(d_scale);
    cudaFree(d_rotation_rad);
    cudaFree(d_rms_px);
    cudaFree(d_best_inliers);
    cudaFree(d_best_index);
    cudaFree(d_refit_inliers);
    cudaFree(d_refit_status);
    cudaFree(d_refit_matrix);
    cudaFree(d_refit_scale);
    cudaFree(d_refit_rotation_rad);
    cudaFree(d_refit_rms_px);
    cudaFree(d_refit_partial_sums);
    cudaFree(d_refit_partial_count);
    cudaFree(d_refit_partial_residual_sums);
    throw;
  }
  cudaFree(d_reference_x);
  cudaFree(d_reference_y);
  cudaFree(d_moving_x);
  cudaFree(d_moving_y);
  cudaFree(d_candidate_params);
  cudaFree(d_candidate_scores);
  cudaFree(d_candidate_rms);
  cudaFree(d_matrix);
  cudaFree(d_scale);
  cudaFree(d_rotation_rad);
  cudaFree(d_rms_px);
  cudaFree(d_best_inliers);
  cudaFree(d_best_index);
  cudaFree(d_refit_inliers);
  cudaFree(d_refit_status);
  cudaFree(d_refit_matrix);
  cudaFree(d_refit_scale);
  cudaFree(d_refit_rotation_rad);
  cudaFree(d_refit_rms_px);
  cudaFree(d_refit_partial_sums);
  cudaFree(d_refit_partial_count);
  cudaFree(d_refit_partial_residual_sums);

  py::list matrix_rows;
  for (int row = 0; row < 3; ++row) {
    py::list matrix_row;
    for (int col = 0; col < 3; ++col) {
      matrix_row.append(host_matrix[static_cast<std::size_t>(row * 3 + col)]);
    }
    matrix_rows.append(matrix_row);
  }
  py::dict result;
  result["matrix"] = matrix_rows;
  result["scale"] = scale;
  result["rotation_rad"] = rotation_rad;
  result["rms_px"] = rms_px;
  result["inliers"] = best_inliers;
  result["refined_inliers"] = refit_inliers;
  result["refit_status_code"] = refit_status;
  result["refit_status"] = refit_status == 0 ? "ok" : (refit_status == 3 ? "rejected" : "failed");
  result["refit_rms_px"] = refit_rms_px;
  result["best_candidate_index"] = best_index;
  result["candidate_count"] = candidate_count;
  result["reference_count"] = reference_count;
  result["moving_count"] = moving_count;
  result["tolerance_px"] = tolerance_px;
  result["min_pair_distance"] = min_pair_distance;
  result["prior_dx"] = prior_dx;
  result["prior_dy"] = prior_dy;
  result["prior_radius_px"] = prior_radius_px;
  result["min_scale"] = min_scale;
  result["max_scale"] = max_scale;
  result["max_abs_rotation_rad"] = max_abs_rotation_rad;
  result["top_k"] = top_k;
  result["top_candidates"] = top_candidates;
  result["status"] = best_inliers > 0 ? "ok" : "failed";
  result["model"] = "catalog_pair_similarity_cuda";
  return result;
}

py::array_t<float> local_norm_apply_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float scale,
    float offset) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const std::size_t n = static_cast<std::size_t>(info.shape[0]) * static_cast<std::size_t>(info.shape[1]);
  py::array_t<float> output({info.shape[0], info.shape[1]});
  const py::buffer_info output_info = output.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(local_norm input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(local_norm output)");
    check_cuda(
        cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm input)");
    glass_local_norm_apply_f32_launch(d_input, d_output, n, scale, offset);
    check_cuda(cudaGetLastError(), "local_norm_apply_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "local_norm_apply_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm output)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  return output;
}

py::array_t<float> local_norm_apply_grid_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    py::array_t<float, py::array::c_style | py::array::forcecast> scales,
    py::array_t<float, py::array::c_style | py::array::forcecast> offsets,
    int tile_height,
    int tile_width) {
  const py::buffer_info input_info = input.request();
  const py::buffer_info scales_info = scales.request();
  const py::buffer_info offsets_info = offsets.request();
  if (input_info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (scales_info.ndim != 2 || offsets_info.ndim != 2) {
    throw std::invalid_argument("scales and offsets must have shape (grid_rows, grid_cols)");
  }
  if (scales_info.shape[0] != offsets_info.shape[0] || scales_info.shape[1] != offsets_info.shape[1]) {
    throw std::invalid_argument("scales and offsets shapes must match");
  }
  if (tile_height <= 0 || tile_width <= 0) {
    throw std::invalid_argument("tile dimensions must be positive");
  }
  const int height = static_cast<int>(input_info.shape[0]);
  const int width = static_cast<int>(input_info.shape[1]);
  const int grid_rows = static_cast<int>(scales_info.shape[0]);
  const int grid_cols = static_cast<int>(scales_info.shape[1]);
  if (grid_rows <= 0 || grid_cols <= 0) {
    throw std::invalid_argument("coefficient grid must not be empty");
  }
  const int expected_rows = (height + tile_height - 1) / tile_height;
  const int expected_cols = (width + tile_width - 1) / tile_width;
  if (grid_rows != expected_rows || grid_cols != expected_cols) {
    throw std::invalid_argument("coefficient grid shape does not match image shape and tile dimensions");
  }

  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  const std::size_t coefficient_count =
      static_cast<std::size_t>(grid_rows) * static_cast<std::size_t>(grid_cols);
  py::array_t<float> output({input_info.shape[0], input_info.shape[1]});
  const py::buffer_info output_info = output.request();

  float* d_input = nullptr;
  float* d_output = nullptr;
  float* d_scales = nullptr;
  float* d_offsets = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(local_norm_grid input)");
    check_cuda(cudaMalloc(&d_output, n * sizeof(float)), "cudaMalloc(local_norm_grid output)");
    check_cuda(
        cudaMalloc(&d_scales, coefficient_count * sizeof(float)),
        "cudaMalloc(local_norm_grid scales)");
    check_cuda(
        cudaMalloc(&d_offsets, coefficient_count * sizeof(float)),
        "cudaMalloc(local_norm_grid offsets)");
    check_cuda(
        cudaMemcpy(d_input, input_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm_grid input)");
    check_cuda(
        cudaMemcpy(d_scales, scales_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm_grid scales)");
    check_cuda(
        cudaMemcpy(d_offsets, offsets_info.ptr, coefficient_count * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm_grid offsets)");
    glass_local_norm_apply_grid_f32_launch(
        d_input,
        d_output,
        d_scales,
        d_offsets,
        width,
        height,
        tile_width,
        tile_height,
        grid_cols,
        grid_rows);
    check_cuda(cudaGetLastError(), "local_norm_apply_grid_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "local_norm_apply_grid_f32 synchronize");
    check_cuda(
        cudaMemcpy(output_info.ptr, d_output, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm_grid output)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_scales);
    cudaFree(d_offsets);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_output);
  cudaFree(d_scales);
  cudaFree(d_offsets);
  return output;
}

py::dict local_norm_pair_stats_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> source,
    py::array_t<float, py::array::c_style | py::array::forcecast> reference) {
  const py::buffer_info source_info = source.request();
  const py::buffer_info reference_info = reference.request();
  if (source_info.ndim != 2 || reference_info.ndim != 2) {
    throw std::invalid_argument("source and reference must have shape (height, width)");
  }
  if (source_info.shape[0] != reference_info.shape[0] || source_info.shape[1] != reference_info.shape[1]) {
    throw std::invalid_argument("source and reference shapes must match");
  }
  const std::size_t n =
      static_cast<std::size_t>(source_info.shape[0]) * static_cast<std::size_t>(source_info.shape[1]);
  if (n == 0) {
    throw std::invalid_argument("cannot compute local normalization stats for an empty tile");
  }

  constexpr int threads = 256;
  const int blocks = std::min<int>(
      4096,
      static_cast<int>((n + static_cast<std::size_t>(threads) - 1) / threads));
  std::vector<double> partial_source_sum(static_cast<std::size_t>(blocks), 0.0);
  std::vector<double> partial_source_sum2(static_cast<std::size_t>(blocks), 0.0);
  std::vector<double> partial_reference_sum(static_cast<std::size_t>(blocks), 0.0);
  std::vector<double> partial_reference_sum2(static_cast<std::size_t>(blocks), 0.0);
  std::vector<unsigned long long> partial_count(static_cast<std::size_t>(blocks), 0);

  float* d_source = nullptr;
  float* d_reference = nullptr;
  double* d_partial_source_sum = nullptr;
  double* d_partial_source_sum2 = nullptr;
  double* d_partial_reference_sum = nullptr;
  double* d_partial_reference_sum2 = nullptr;
  unsigned long long* d_partial_count = nullptr;
  try {
    check_cuda(cudaMalloc(&d_source, n * sizeof(float)), "cudaMalloc(local_norm source)");
    check_cuda(cudaMalloc(&d_reference, n * sizeof(float)), "cudaMalloc(local_norm reference)");
    check_cuda(
        cudaMemcpy(d_source, source_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm source)");
    check_cuda(
        cudaMemcpy(d_reference, reference_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(local_norm reference)");
    check_cuda(
        cudaMalloc(&d_partial_source_sum, partial_source_sum.size() * sizeof(double)),
        "cudaMalloc(local_norm source sum)");
    check_cuda(
        cudaMalloc(&d_partial_source_sum2, partial_source_sum2.size() * sizeof(double)),
        "cudaMalloc(local_norm source sum2)");
    check_cuda(
        cudaMalloc(&d_partial_reference_sum, partial_reference_sum.size() * sizeof(double)),
        "cudaMalloc(local_norm reference sum)");
    check_cuda(
        cudaMalloc(&d_partial_reference_sum2, partial_reference_sum2.size() * sizeof(double)),
        "cudaMalloc(local_norm reference sum2)");
    check_cuda(
        cudaMalloc(&d_partial_count, partial_count.size() * sizeof(unsigned long long)),
        "cudaMalloc(local_norm count)");
    glass_pair_sum_stats_f32_launch(
        d_source,
        d_reference,
        d_partial_source_sum,
        d_partial_source_sum2,
        d_partial_reference_sum,
        d_partial_reference_sum2,
        d_partial_count,
        n,
        blocks);
    check_cuda(cudaGetLastError(), "local_norm_pair_stats_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "local_norm_pair_stats_f32 synchronize");
    check_cuda(
        cudaMemcpy(
            partial_source_sum.data(),
            d_partial_source_sum,
            partial_source_sum.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm source sum)");
    check_cuda(
        cudaMemcpy(
            partial_source_sum2.data(),
            d_partial_source_sum2,
            partial_source_sum2.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm source sum2)");
    check_cuda(
        cudaMemcpy(
            partial_reference_sum.data(),
            d_partial_reference_sum,
            partial_reference_sum.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm reference sum)");
    check_cuda(
        cudaMemcpy(
            partial_reference_sum2.data(),
            d_partial_reference_sum2,
            partial_reference_sum2.size() * sizeof(double),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm reference sum2)");
    check_cuda(
        cudaMemcpy(
            partial_count.data(),
            d_partial_count,
            partial_count.size() * sizeof(unsigned long long),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(local_norm count)");
  } catch (...) {
    cudaFree(d_source);
    cudaFree(d_reference);
    cudaFree(d_partial_source_sum);
    cudaFree(d_partial_source_sum2);
    cudaFree(d_partial_reference_sum);
    cudaFree(d_partial_reference_sum2);
    cudaFree(d_partial_count);
    throw;
  }
  cudaFree(d_source);
  cudaFree(d_reference);
  cudaFree(d_partial_source_sum);
  cudaFree(d_partial_source_sum2);
  cudaFree(d_partial_reference_sum);
  cudaFree(d_partial_reference_sum2);
  cudaFree(d_partial_count);

  double source_sum = 0.0;
  double source_sum2 = 0.0;
  double reference_sum = 0.0;
  double reference_sum2 = 0.0;
  unsigned long long count = 0;
  for (std::size_t i = 0; i < partial_count.size(); ++i) {
    source_sum += partial_source_sum[i];
    source_sum2 += partial_source_sum2[i];
    reference_sum += partial_reference_sum[i];
    reference_sum2 += partial_reference_sum2[i];
    count += partial_count[i];
  }
  py::dict result;
  result["valid_pixels"] = static_cast<unsigned long long>(count);
  result["total_pixels"] = static_cast<unsigned long long>(n);
  result["model"] = "cuda_pair_mean_std";
  if (count == 0) {
    result["source_mean"] = py::none();
    result["reference_mean"] = py::none();
    result["source_std"] = py::none();
    result["reference_std"] = py::none();
    return result;
  }
  const double inv_count = 1.0 / static_cast<double>(count);
  const double source_mean = source_sum * inv_count;
  const double reference_mean = reference_sum * inv_count;
  const double source_var = std::max(0.0, source_sum2 * inv_count - source_mean * source_mean);
  const double reference_var = std::max(0.0, reference_sum2 * inv_count - reference_mean * reference_mean);
  result["source_mean"] = source_mean;
  result["reference_mean"] = reference_mean;
  result["source_std"] = std::sqrt(source_var);
  result["reference_std"] = std::sqrt(reference_var);
  return result;
}

py::tuple integrate_accumulate_mean_tile_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> frame_tile,
    py::array_t<float, py::array::c_style | py::array::forcecast> weight_tile,
    py::array_t<float, py::array::c_style | py::array::forcecast> sum_tile,
    py::array_t<float, py::array::c_style | py::array::forcecast> weight_sum_tile) {
  const py::buffer_info frame_info = frame_tile.request();
  const py::buffer_info weight_info = weight_tile.request();
  const py::buffer_info sum_info = sum_tile.request();
  const py::buffer_info weight_sum_info = weight_sum_tile.request();
  if (frame_info.ndim != 2 || weight_info.ndim != 2 || sum_info.ndim != 2 || weight_sum_info.ndim != 2) {
    throw std::invalid_argument("integration tiles must have shape (height, width)");
  }
  if (frame_info.shape != weight_info.shape || frame_info.shape != sum_info.shape ||
      frame_info.shape != weight_sum_info.shape) {
    throw std::invalid_argument("integration tile shapes must match");
  }
  const std::size_t n = static_cast<std::size_t>(frame_info.shape[0]) *
      static_cast<std::size_t>(frame_info.shape[1]);
  py::array_t<float> out_sum({frame_info.shape[0], frame_info.shape[1]});
  py::array_t<float> out_weight({frame_info.shape[0], frame_info.shape[1]});
  const py::buffer_info out_sum_info = out_sum.request();
  const py::buffer_info out_weight_info = out_weight.request();

  float* d_frame = nullptr;
  float* d_weight = nullptr;
  float* d_sum = nullptr;
  float* d_weight_sum = nullptr;
  try {
    check_cuda(cudaMalloc(&d_frame, n * sizeof(float)), "cudaMalloc(integration frame)");
    check_cuda(cudaMalloc(&d_weight, n * sizeof(float)), "cudaMalloc(integration weight)");
    check_cuda(cudaMalloc(&d_sum, n * sizeof(float)), "cudaMalloc(integration sum)");
    check_cuda(cudaMalloc(&d_weight_sum, n * sizeof(float)), "cudaMalloc(integration weight sum)");
    check_cuda(cudaMemcpy(d_frame, frame_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(frame)");
    check_cuda(cudaMemcpy(d_weight, weight_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(weight)");
    check_cuda(cudaMemcpy(d_sum, sum_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(sum)");
    check_cuda(
        cudaMemcpy(d_weight_sum, weight_sum_info.ptr, n * sizeof(float), cudaMemcpyHostToDevice),
        "cudaMemcpy(weight sum)");
    glass_integrate_accumulate_mean_tile_f32_launch(d_frame, d_weight, d_sum, d_weight_sum, n);
    check_cuda(cudaGetLastError(), "integrate_accumulate_mean_tile_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "integrate_accumulate_mean_tile_f32 synchronize");
    check_cuda(
        cudaMemcpy(out_sum_info.ptr, d_sum, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(out sum)");
    check_cuda(
        cudaMemcpy(out_weight_info.ptr, d_weight_sum, n * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(out weight sum)");
  } catch (...) {
    cudaFree(d_frame);
    cudaFree(d_weight);
    cudaFree(d_sum);
    cudaFree(d_weight_sum);
    throw;
  }
  cudaFree(d_frame);
  cudaFree(d_weight);
  cudaFree(d_sum);
  cudaFree(d_weight_sum);
  return py::make_tuple(out_sum, out_weight);
}

py::array_t<unsigned char> star_local_max_mask_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<unsigned char> mask({info.shape[0], info.shape[1]});
  const py::buffer_info mask_info = mask.request();

  float* d_input = nullptr;
  unsigned char* d_mask = nullptr;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(star input)");
    check_cuda(cudaMalloc(&d_mask, n * sizeof(unsigned char)), "cudaMalloc(star mask)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(star input)");
    glass_star_local_max_mask_f32_launch(d_input, d_mask, width, height, threshold);
    check_cuda(cudaGetLastError(), "star_local_max_mask_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_local_max_mask_f32 synchronize");
    check_cuda(
        cudaMemcpy(mask_info.ptr, d_mask, n * sizeof(unsigned char), cudaMemcpyDeviceToHost),
        "cudaMemcpy(star mask)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_mask);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_mask);
  return mask;
}

py::dict star_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int max_candidates) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (max_candidates <= 0) {
    throw std::invalid_argument("max_candidates must be positive");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_candidates});
  py::array_t<float> ys({max_candidates});
  py::array_t<float> fluxes({max_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int total_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(star input)");
    check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star xs)");
    check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
        "cudaMalloc(star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(star count)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(star input)");
    glass_star_candidates_f32_launch(
        d_input, d_xs, d_ys, d_fluxes, d_count, width, height, threshold, max_candidates);
    check_cuda(cudaGetLastError(), "star_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(star count)");
    const int stored_count = total_count < max_candidates ? total_count : max_candidates;
    check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star xs)");
    check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star ys)");
    check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    throw;
  }
}

py::dict star_top_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int max_candidates) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (max_candidates <= 0) {
    throw std::invalid_argument("max_candidates must be positive");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_candidates});
  py::array_t<float> ys({max_candidates});
  py::array_t<float> fluxes({max_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_lock = nullptr;
  int total_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(top star input)");
    check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star xs)");
    check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(max_candidates) * sizeof(float)), "cudaMalloc(top star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_candidates) * sizeof(float)),
        "cudaMalloc(top star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(top star count)");
    check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(top star lock)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(top star input)");
    glass_star_top_candidates_f32_launch(
        d_input, d_xs, d_ys, d_fluxes, d_count, d_lock, width, height, threshold, max_candidates);
    check_cuda(cudaGetLastError(), "star_top_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_top_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(top star count)");
    const int stored_count = total_count < max_candidates ? total_count : max_candidates;
    check_cuda(cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star xs)");
    check_cuda(cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star ys)");
    check_cuda(cudaMemcpy(flux_info.ptr, d_fluxes, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost), "cudaMemcpy(top star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    throw;
  }
}

py::dict star_top_nms_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int scan_candidates,
    int max_output_candidates,
    float min_separation_px) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (scan_candidates <= 0 || max_output_candidates <= 0) {
    throw std::invalid_argument("candidate counts must be positive");
  }
  if (scan_candidates < max_output_candidates) {
    throw std::invalid_argument("scan_candidates must be greater than or equal to max_output_candidates");
  }
  if (min_separation_px < 0.0f) {
    throw std::invalid_argument("min_separation_px must be non-negative");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_output_candidates});
  py::array_t<float> ys({max_output_candidates});
  py::array_t<float> fluxes({max_output_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_scan_xs = nullptr;
  float* d_scan_ys = nullptr;
  float* d_scan_fluxes = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_lock = nullptr;
  int* d_stored_count = nullptr;
  int total_count = 0;
  int stored_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(top nms star input)");
    check_cuda(
        cudaMalloc(&d_scan_xs, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
        "cudaMalloc(top nms scan xs)");
    check_cuda(
        cudaMalloc(&d_scan_ys, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
        "cudaMalloc(top nms scan ys)");
    check_cuda(
        cudaMalloc(&d_scan_fluxes, static_cast<std::size_t>(scan_candidates) * sizeof(float)),
        "cudaMalloc(top nms scan fluxes)");
    check_cuda(
        cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(top nms star xs)");
    check_cuda(
        cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(top nms star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(top nms star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(top nms star count)");
    check_cuda(cudaMalloc(&d_lock, sizeof(int)), "cudaMalloc(top nms star lock)");
    check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(top nms stored count)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(top nms star input)");
    glass_star_top_nms_candidates_f32_launch(
        d_input,
        d_scan_xs,
        d_scan_ys,
        d_scan_fluxes,
        d_xs,
        d_ys,
        d_fluxes,
        d_count,
        d_lock,
        d_stored_count,
        width,
        height,
        threshold,
        scan_candidates,
        max_output_candidates,
        min_separation_px);
    check_cuda(cudaGetLastError(), "star_top_nms_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_top_nms_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(top nms count)");
    check_cuda(
        cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms stored count)");
    check_cuda(
        cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms star xs)");
    check_cuda(
        cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms star ys)");
    check_cuda(
        cudaMemcpy(
            flux_info.ptr,
            d_fluxes,
            static_cast<std::size_t>(stored_count) * sizeof(float),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(top nms star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["scan_candidates"] = scan_candidates;
    result["max_output_candidates"] = max_output_candidates;
    result["min_separation_px"] = min_separation_px;
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_scan_xs);
    cudaFree(d_scan_ys);
    cudaFree(d_scan_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    cudaFree(d_stored_count);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_scan_xs);
    cudaFree(d_scan_ys);
    cudaFree(d_scan_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_lock);
    cudaFree(d_stored_count);
    throw;
  }
}

py::dict star_grid_top_nms_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int grid_cols,
    int grid_rows,
    int candidates_per_cell,
    int max_output_candidates,
    float min_separation_px) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (grid_cols <= 0 || grid_rows <= 0 || candidates_per_cell <= 0 || max_output_candidates <= 0) {
    throw std::invalid_argument("grid dimensions and candidate counts must be positive");
  }
  if (min_separation_px < 0.0f) {
    throw std::invalid_argument("min_separation_px must be non-negative");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const int cell_count = grid_cols * grid_rows;
  const int grid_capacity = cell_count * candidates_per_cell;
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({max_output_candidates});
  py::array_t<float> ys({max_output_candidates});
  py::array_t<float> fluxes({max_output_candidates});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_grid_xs = nullptr;
  float* d_grid_ys = nullptr;
  float* d_grid_fluxes = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_locks = nullptr;
  int* d_cell_counts = nullptr;
  int* d_stored_count = nullptr;
  int total_count = 0;
  int stored_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(grid top nms input)");
    check_cuda(
        cudaMalloc(&d_grid_xs, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
        "cudaMalloc(grid top nms grid xs)");
    check_cuda(
        cudaMalloc(&d_grid_ys, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
        "cudaMalloc(grid top nms grid ys)");
    check_cuda(
        cudaMalloc(&d_grid_fluxes, static_cast<std::size_t>(grid_capacity) * sizeof(float)),
        "cudaMalloc(grid top nms grid fluxes)");
    check_cuda(
        cudaMalloc(&d_xs, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(grid top nms star xs)");
    check_cuda(
        cudaMalloc(&d_ys, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(grid top nms star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(max_output_candidates) * sizeof(float)),
        "cudaMalloc(grid top nms star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(grid top nms star count)");
    check_cuda(cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)), "cudaMalloc(grid top nms locks)");
    check_cuda(
        cudaMalloc(&d_cell_counts, static_cast<std::size_t>(cell_count) * sizeof(int)),
        "cudaMalloc(grid top nms cell counts)");
    check_cuda(cudaMalloc(&d_stored_count, sizeof(int)), "cudaMalloc(grid top nms stored count)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(grid top nms input)");
    glass_star_grid_top_nms_candidates_f32_launch(
        d_input,
        d_grid_xs,
        d_grid_ys,
        d_grid_fluxes,
        d_xs,
        d_ys,
        d_fluxes,
        d_count,
        d_locks,
        d_cell_counts,
        d_stored_count,
        width,
        height,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px);
    check_cuda(cudaGetLastError(), "star_grid_top_nms_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_grid_top_nms_candidates_f32 synchronize");
    check_cuda(
        cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms count)");
    check_cuda(
        cudaMemcpy(&stored_count, d_stored_count, sizeof(int), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms stored count)");
    check_cuda(
        cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms star xs)");
    check_cuda(
        cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(stored_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms star ys)");
    check_cuda(
        cudaMemcpy(
            flux_info.ptr,
            d_fluxes,
            static_cast<std::size_t>(stored_count) * sizeof(float),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid top nms star fluxes)");
    py::dict result;
    result["count"] = total_count;
    result["stored_count"] = stored_count;
    result["grid_cols"] = grid_cols;
    result["grid_rows"] = grid_rows;
    result["candidates_per_cell"] = candidates_per_cell;
    result["grid_capacity"] = grid_capacity;
    result["max_output_candidates"] = max_output_candidates;
    result["min_separation_px"] = min_separation_px;
    result["catalog_sort_mode"] = grid_catalog_sort_mode(grid_capacity);
    result["catalog_topk_mode"] = grid_catalog_topk_mode();
    result["x"] = xs[py::slice(0, stored_count, 1)];
    result["y"] = ys[py::slice(0, stored_count, 1)];
    result["flux"] = fluxes[py::slice(0, stored_count, 1)];
    cudaFree(d_input);
    cudaFree(d_grid_xs);
    cudaFree(d_grid_ys);
    cudaFree(d_grid_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_locks);
    cudaFree(d_cell_counts);
    cudaFree(d_stored_count);
    return result;
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_grid_xs);
    cudaFree(d_grid_ys);
    cudaFree(d_grid_fluxes);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_locks);
    cudaFree(d_cell_counts);
    cudaFree(d_stored_count);
    throw;
  }
}

py::dict star_grid_candidates_f32(
    py::array_t<float, py::array::c_style | py::array::forcecast> input,
    float threshold,
    int grid_cols,
    int grid_rows) {
  const py::buffer_info info = input.request();
  if (info.ndim != 2) {
    throw std::invalid_argument("input must have shape (height, width)");
  }
  if (grid_cols <= 0 || grid_rows <= 0) {
    throw std::invalid_argument("grid dimensions must be positive");
  }
  const int height = static_cast<int>(info.shape[0]);
  const int width = static_cast<int>(info.shape[1]);
  const int cell_count = grid_cols * grid_rows;
  const std::size_t n = static_cast<std::size_t>(height) * static_cast<std::size_t>(width);
  py::array_t<float> xs({cell_count});
  py::array_t<float> ys({cell_count});
  py::array_t<float> fluxes({cell_count});
  const py::buffer_info xs_info = xs.request();
  const py::buffer_info ys_info = ys.request();
  const py::buffer_info flux_info = fluxes.request();

  float* d_input = nullptr;
  float* d_xs = nullptr;
  float* d_ys = nullptr;
  float* d_fluxes = nullptr;
  int* d_count = nullptr;
  int* d_locks = nullptr;
  int total_count = 0;
  try {
    check_cuda(cudaMalloc(&d_input, n * sizeof(float)), "cudaMalloc(grid star input)");
    check_cuda(cudaMalloc(&d_xs, static_cast<std::size_t>(cell_count) * sizeof(float)), "cudaMalloc(grid star xs)");
    check_cuda(cudaMalloc(&d_ys, static_cast<std::size_t>(cell_count) * sizeof(float)), "cudaMalloc(grid star ys)");
    check_cuda(
        cudaMalloc(&d_fluxes, static_cast<std::size_t>(cell_count) * sizeof(float)),
        "cudaMalloc(grid star fluxes)");
    check_cuda(cudaMalloc(&d_count, sizeof(int)), "cudaMalloc(grid star count)");
    check_cuda(cudaMalloc(&d_locks, static_cast<std::size_t>(cell_count) * sizeof(int)), "cudaMalloc(grid star locks)");
    check_cuda(cudaMemcpy(d_input, info.ptr, n * sizeof(float), cudaMemcpyHostToDevice), "cudaMemcpy(grid star input)");
    glass_star_grid_candidates_f32_launch(
        d_input,
        d_xs,
        d_ys,
        d_fluxes,
        d_count,
        d_locks,
        width,
        height,
        threshold,
        grid_cols,
        grid_rows);
    check_cuda(cudaGetLastError(), "star_grid_candidates_f32 kernel launch");
    check_cuda(cudaDeviceSynchronize(), "star_grid_candidates_f32 synchronize");
    check_cuda(cudaMemcpy(&total_count, d_count, sizeof(int), cudaMemcpyDeviceToHost), "cudaMemcpy(grid star count)");
    check_cuda(
        cudaMemcpy(xs_info.ptr, d_xs, static_cast<std::size_t>(cell_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid star xs)");
    check_cuda(
        cudaMemcpy(ys_info.ptr, d_ys, static_cast<std::size_t>(cell_count) * sizeof(float), cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid star ys)");
    check_cuda(
        cudaMemcpy(
            flux_info.ptr,
            d_fluxes,
            static_cast<std::size_t>(cell_count) * sizeof(float),
            cudaMemcpyDeviceToHost),
        "cudaMemcpy(grid star fluxes)");
  } catch (...) {
    cudaFree(d_input);
    cudaFree(d_xs);
    cudaFree(d_ys);
    cudaFree(d_fluxes);
    cudaFree(d_count);
    cudaFree(d_locks);
    throw;
  }
  cudaFree(d_input);
  cudaFree(d_xs);
  cudaFree(d_ys);
  cudaFree(d_fluxes);
  cudaFree(d_count);
  cudaFree(d_locks);

  int stored_count = 0;
  const auto* flux_ptr = static_cast<const float*>(flux_info.ptr);
  while (stored_count < cell_count && flux_ptr[stored_count] > -1.0e30f) {
    ++stored_count;
  }
  py::dict result;
  result["count"] = total_count;
  result["stored_count"] = stored_count;
  result["x"] = xs[py::slice(0, stored_count, 1)];
  result["y"] = ys[py::slice(0, stored_count, 1)];
  result["flux"] = fluxes[py::slice(0, stored_count, 1)];
  result["grid_cols"] = grid_cols;
  result["grid_rows"] = grid_rows;
  return result;
}

struct HostFloat2D {
  py::array_t<float, py::array::c_style | py::array::forcecast> array;
  const float* data = nullptr;
  py::ssize_t height = 0;
  py::ssize_t width = 0;
  bool present = false;
};

enum class HostCountDType {
  Float32,
  Int16,
  UInt16,
};

struct HostCount2D {
  py::array array;
  const void* data = nullptr;
  py::ssize_t height = 0;
  py::ssize_t width = 0;
  HostCountDType dtype = HostCountDType::Float32;
  std::string dtype_name = "absent";
  bool present = false;

  float value(std::size_t index) const {
    if (dtype == HostCountDType::Float32) {
      return static_cast<const float*>(data)[index];
    }
    if (dtype == HostCountDType::UInt16) {
      return static_cast<float>(static_cast<const std::uint16_t*>(data)[index]);
    }
    return static_cast<float>(static_cast<const std::int16_t*>(data)[index]);
  }
};

struct HostCoverageStats {
  std::size_t total_pixels = 0;
  std::size_t finite_pixels = 0;
  long long rounded_sum = 0;
  double min = 0.0;
  double max = 0.0;
  double mean = 0.0;
};

struct HostCountMapStats {
  bool present = false;
  std::size_t total_pixels = 0;
  std::size_t finite_pixels = 0;
  long long rounded_sum = 0;
  std::size_t positive_pixels = 0;
  std::size_t negative_pixels = 0;
  std::size_t fractional_pixels = 0;
  double min = 0.0;
  double max = 0.0;
};

struct HostDqMapStats {
  HostCoverageStats post_rejection_coverage;
  HostCoverageStats geometric_warp_coverage;
  HostCountMapStats low_rejection;
  HostCountMapStats high_rejection;
  std::size_t post_rejection_zero_pixels = 0;
  std::size_t geometric_zero_pixels = 0;
  std::size_t geometric_partial_pixels = 0;
  std::size_t geometric_full_pixels = 0;
  std::size_t no_data_pixels = 0;
  std::size_t warp_edge_pixels = 0;
  std::size_t low_rejected_pixels = 0;
  std::size_t high_rejected_pixels = 0;
  std::size_t rejection_reduced_pixels = 0;
  std::size_t valid_pixels = 0;
};

HostFloat2D require_host_float2d(py::object object, const std::string& name) {
  auto array = py::array_t<float, py::array::c_style | py::array::forcecast>::ensure(object);
  if (!array) {
    throw std::invalid_argument(name + " must be convertible to a float32 C-contiguous array");
  }
  const py::buffer_info info = array.request();
  if (info.ndim != 2) {
    throw std::invalid_argument(name + " must have shape (height, width)");
  }
  HostFloat2D result;
  result.array = array;
  result.data = static_cast<const float*>(info.ptr);
  result.height = info.shape[0];
  result.width = info.shape[1];
  result.present = true;
  return result;
}

HostFloat2D optional_host_float2d(py::object object, const std::string& name) {
  if (object.is_none()) {
    return HostFloat2D();
  }
  return require_host_float2d(object, name);
}

HostCount2D require_host_count2d(py::object object, const std::string& name) {
  py::array array = py::array::ensure(object);
  if (!array) {
    throw std::invalid_argument(name + " must be convertible to a C-contiguous count-map array");
  }
  const py::buffer_info info = array.request();
  if (info.ndim != 2) {
    throw std::invalid_argument(name + " must have shape (height, width)");
  }
  if (info.strides[1] != info.itemsize || info.strides[0] != info.itemsize * info.shape[1]) {
    throw std::invalid_argument(name + " must be C-contiguous");
  }
  const std::string dtype_name = py::str(array.dtype()).cast<std::string>();
  HostCountDType dtype = HostCountDType::Float32;
  if (dtype_name == "float32") {
    dtype = HostCountDType::Float32;
  } else if (dtype_name == "uint16") {
    dtype = HostCountDType::UInt16;
  } else if (dtype_name == "int16") {
    dtype = HostCountDType::Int16;
  } else {
    throw std::invalid_argument(name + " must have dtype float32, int16, or uint16");
  }
  HostCount2D result;
  result.array = array;
  result.data = info.ptr;
  result.height = info.shape[0];
  result.width = info.shape[1];
  result.dtype = dtype;
  result.dtype_name = dtype_name;
  result.present = true;
  return result;
}

HostCount2D optional_host_count2d(py::object object, const std::string& name) {
  if (object.is_none()) {
    return HostCount2D();
  }
  return require_host_count2d(object, name);
}

void require_same_shape(const HostFloat2D& candidate, const HostFloat2D& reference, const std::string& name) {
  if (candidate.present && (candidate.height != reference.height || candidate.width != reference.width)) {
    std::ostringstream stream;
    stream << name << " shape " << candidate.height << "x" << candidate.width << " does not match master shape "
           << reference.height << "x" << reference.width;
    throw std::invalid_argument(stream.str());
  }
}

void require_same_shape(const HostCount2D& candidate, const HostFloat2D& reference, const std::string& name) {
  if (candidate.present && (candidate.height != reference.height || candidate.width != reference.width)) {
    std::ostringstream stream;
    stream << name << " shape " << candidate.height << "x" << candidate.width << " does not match master shape "
           << reference.height << "x" << reference.width;
    throw std::invalid_argument(stream.str());
  }
}

void update_coverage_stats(HostCoverageStats& stats, float value) {
  ++stats.total_pixels;
  if (!std::isfinite(value)) {
    return;
  }
  const double as_double = static_cast<double>(value);
  if (stats.finite_pixels == 0) {
    stats.min = as_double;
    stats.max = as_double;
  } else {
    stats.min = std::min(stats.min, as_double);
    stats.max = std::max(stats.max, as_double);
  }
  ++stats.finite_pixels;
  stats.mean += as_double;
  stats.rounded_sum += static_cast<long long>(std::nearbyint(as_double));
}

void update_count_map_stats(HostCountMapStats& stats, float value) {
  ++stats.total_pixels;
  if (!std::isfinite(value)) {
    return;
  }
  const double as_double = static_cast<double>(value);
  const double rounded = std::nearbyint(as_double);
  if (stats.finite_pixels == 0) {
    stats.min = as_double;
    stats.max = as_double;
  } else {
    stats.min = std::min(stats.min, as_double);
    stats.max = std::max(stats.max, as_double);
  }
  ++stats.finite_pixels;
  if (value > 0.0f) {
    ++stats.positive_pixels;
  }
  if (value < 0.0f) {
    ++stats.negative_pixels;
  }
  if (std::abs(as_double - rounded) > 1.0e-3) {
    ++stats.fractional_pixels;
  }
  stats.rounded_sum += static_cast<long long>(std::max(rounded, 0.0));
}

py::dict coverage_stats_to_dict(const HostCoverageStats& stats) {
  py::dict result;
  result["total_pixels"] = stats.total_pixels;
  result["finite_pixels"] = stats.finite_pixels;
  result["rounded_sum"] = stats.rounded_sum;
  if (stats.finite_pixels == 0) {
    result["min"] = 0.0;
    result["max"] = 0.0;
    result["mean"] = 0.0;
  } else {
    result["min"] = stats.min;
    result["max"] = stats.max;
    result["mean"] = static_cast<float>(stats.mean / static_cast<double>(stats.finite_pixels));
  }
  return result;
}

py::dict count_map_stats_to_dict(const HostCountMapStats& stats, py::ssize_t height, py::ssize_t width) {
  py::dict result;
  result["present"] = true;
  py::list shape;
  shape.append(height);
  shape.append(width);
  result["shape"] = shape;
  result["dtype"] = "float32";
  result["finite_pixels"] = stats.finite_pixels;
  result["nonfinite_pixels"] = stats.total_pixels - stats.finite_pixels;
  if (stats.finite_pixels == 0) {
    result["min"] = py::none();
    result["max"] = py::none();
  } else {
    result["min"] = stats.min;
    result["max"] = stats.max;
  }
  result["rounded_sum"] = stats.rounded_sum;
  result["positive_pixels"] = stats.positive_pixels;
  result["zero_or_less_pixels"] = stats.total_pixels - stats.positive_pixels;
  result["negative_pixels"] = stats.negative_pixels;
  result["fractional_pixels"] = stats.fractional_pixels;
  result["stats_source"] = "resident_precomputed_count_map";
  result["stats_profile"] = "count_map_contract_fields";
  result["stats_backend"] = "native_host";
  return result;
}

py::dict absent_count_map_stats() {
  py::dict result;
  result["present"] = false;
  return result;
}

void update_finite_coverage_stats(HostCoverageStats& stats, float value) {
  ++stats.total_pixels;
  const double as_double = static_cast<double>(value);
  if (stats.finite_pixels == 0) {
    stats.min = as_double;
    stats.max = as_double;
  } else {
    stats.min = std::min(stats.min, as_double);
    stats.max = std::max(stats.max, as_double);
  }
  ++stats.finite_pixels;
  stats.mean += as_double;
  stats.rounded_sum += static_cast<long long>(std::nearbyint(as_double));
}

void update_finite_nonnegative_count_stats(HostCountMapStats& stats, float value) {
  stats.present = true;
  ++stats.total_pixels;
  const double as_double = static_cast<double>(value);
  if (stats.finite_pixels == 0) {
    stats.min = as_double;
    stats.max = as_double;
  } else {
    stats.min = std::min(stats.min, as_double);
    stats.max = std::max(stats.max, as_double);
  }
  ++stats.finite_pixels;
  if (value > 0.0f) {
    ++stats.positive_pixels;
  }
  stats.rounded_sum += static_cast<long long>(std::nearbyint(as_double));
}

void merge_coverage_stats(HostCoverageStats& target, const HostCoverageStats& source) {
  target.total_pixels += source.total_pixels;
  if (source.finite_pixels == 0) {
    return;
  }
  if (target.finite_pixels == 0) {
    target.min = source.min;
    target.max = source.max;
  } else {
    target.min = std::min(target.min, source.min);
    target.max = std::max(target.max, source.max);
  }
  target.finite_pixels += source.finite_pixels;
  target.mean += source.mean;
  target.rounded_sum += source.rounded_sum;
}

void merge_count_map_stats(HostCountMapStats& target, const HostCountMapStats& source) {
  target.present = target.present || source.present;
  target.total_pixels += source.total_pixels;
  if (source.finite_pixels > 0) {
    if (target.finite_pixels == 0) {
      target.min = source.min;
      target.max = source.max;
    } else {
      target.min = std::min(target.min, source.min);
      target.max = std::max(target.max, source.max);
    }
  }
  target.finite_pixels += source.finite_pixels;
  target.rounded_sum += source.rounded_sum;
  target.positive_pixels += source.positive_pixels;
  target.negative_pixels += source.negative_pixels;
  target.fractional_pixels += source.fractional_pixels;
}

void merge_dq_map_stats(HostDqMapStats& target, const HostDqMapStats& source) {
  merge_coverage_stats(target.post_rejection_coverage, source.post_rejection_coverage);
  merge_coverage_stats(target.geometric_warp_coverage, source.geometric_warp_coverage);
  merge_count_map_stats(target.low_rejection, source.low_rejection);
  merge_count_map_stats(target.high_rejection, source.high_rejection);
  target.post_rejection_zero_pixels += source.post_rejection_zero_pixels;
  target.geometric_zero_pixels += source.geometric_zero_pixels;
  target.geometric_partial_pixels += source.geometric_partial_pixels;
  target.geometric_full_pixels += source.geometric_full_pixels;
  target.no_data_pixels += source.no_data_pixels;
  target.warp_edge_pixels += source.warp_edge_pixels;
  target.low_rejected_pixels += source.low_rejected_pixels;
  target.high_rejected_pixels += source.high_rejected_pixels;
  target.rejection_reduced_pixels += source.rejection_reduced_pixels;
  target.valid_pixels += source.valid_pixels;
}

py::dict finite_nonnegative_count_map_stats_to_dict(
    const HostCountMapStats& stats,
    py::ssize_t height,
    py::ssize_t width,
    const std::string& dtype_name = "float32") {
  py::dict result;
  result["present"] = true;
  py::list shape;
  shape.append(height);
  shape.append(width);
  result["shape"] = shape;
  result["dtype"] = dtype_name;
  result["finite_pixels"] = stats.total_pixels;
  result["nonfinite_pixels"] = 0;
  if (stats.total_pixels == 0) {
    result["min"] = py::none();
    result["max"] = py::none();
  } else {
    result["min"] = stats.min;
    result["max"] = stats.max;
  }
  result["rounded_sum"] = stats.rounded_sum;
  result["positive_pixels"] = stats.positive_pixels;
  result["zero_or_less_pixels"] = stats.total_pixels - stats.positive_pixels;
  result["negative_pixels"] = 0;
  result["fractional_pixels"] = 0;
  result["stats_source"] = "resident_precomputed_count_map";
  result["stats_profile"] = "resident_finite_integer_count_map_fast_path";
  result["stats_backend"] = "native_host_fast_count_maps";
  return result;
}

py::tuple resident_dq_map_count_maps_i16(
    py::object master_obj,
    py::object coverage_map_obj,
    py::object low_rejection_map_obj,
    py::object high_rejection_map_obj,
    py::object geometric_warp_coverage_map_obj,
    int active_frame_count) {
  const HostFloat2D master = require_host_float2d(master_obj, "master");
  const HostCount2D coverage_map = optional_host_count2d(coverage_map_obj, "coverage_map");
  const HostCount2D low_rejection_map = optional_host_count2d(low_rejection_map_obj, "low_rejection_map");
  const HostCount2D high_rejection_map = optional_host_count2d(high_rejection_map_obj, "high_rejection_map");
  const HostCount2D geometric_warp_coverage_map =
      optional_host_count2d(geometric_warp_coverage_map_obj, "geometric_warp_coverage_map");
  require_same_shape(coverage_map, master, "coverage_map");
  require_same_shape(low_rejection_map, master, "low_rejection_map");
  require_same_shape(high_rejection_map, master, "high_rejection_map");
  require_same_shape(geometric_warp_coverage_map, master, "geometric_warp_coverage_map");

  constexpr std::int16_t dq_no_data = static_cast<std::int16_t>(1u << 0);
  constexpr std::int16_t dq_warp_edge = static_cast<std::int16_t>(1u << 6);
  constexpr std::int16_t dq_low_rejected = static_cast<std::int16_t>(1u << 8);
  constexpr std::int16_t dq_high_rejected = static_cast<std::int16_t>(1u << 9);
  const std::size_t total_pixels =
      static_cast<std::size_t>(master.height) * static_cast<std::size_t>(master.width);
  py::array_t<std::int16_t> dq({master.height, master.width});
  const py::buffer_info dq_info = dq.request();
  auto* dq_data = static_cast<std::int16_t*>(dq_info.ptr);
  HostDqMapStats loop_stats;
  const int expected_count = active_frame_count > 0 ? active_frame_count : 0;
  const float full_threshold = expected_count > 0 ? static_cast<float>(expected_count) - 0.5f : 0.0f;
  const unsigned int hardware_threads = std::max(1u, std::thread::hardware_concurrency());
  std::size_t thread_count = 1;
  if (total_pixels >= 1024u * 1024u) {
    const std::size_t chunk_limited_threads = (total_pixels + (1024u * 1024u) - 1u) / (1024u * 1024u);
    thread_count = std::min<std::size_t>(16u, std::min<std::size_t>(hardware_threads, chunk_limited_threads));
    thread_count = std::max<std::size_t>(1u, thread_count);
  }

  {
    py::gil_scoped_release release;
    auto scan_range = [&](std::size_t begin, std::size_t end, HostDqMapStats& stats) {
      for (std::size_t index = begin; index < end; ++index) {
        std::int16_t flags = 0;
        bool invalid = false;

        if (coverage_map.present) {
          const float coverage = coverage_map.value(index);
          update_finite_coverage_stats(stats.post_rejection_coverage, coverage);
          if (coverage <= 0.5f) {
            invalid = true;
            flags = static_cast<std::int16_t>(flags | dq_warp_edge);
            ++stats.post_rejection_zero_pixels;
          }
        }

        if (geometric_warp_coverage_map.present) {
          const float geometric = geometric_warp_coverage_map.value(index);
          update_finite_coverage_stats(stats.geometric_warp_coverage, geometric);
          if (geometric <= 0.5f) {
            invalid = true;
            flags = static_cast<std::int16_t>(flags | dq_warp_edge);
            ++stats.geometric_zero_pixels;
          } else if (expected_count > 0) {
            if (geometric < full_threshold) {
              flags = static_cast<std::int16_t>(flags | dq_warp_edge);
              ++stats.geometric_partial_pixels;
            } else {
              ++stats.geometric_full_pixels;
            }
          }
        }

        if (invalid) {
          flags = static_cast<std::int16_t>(flags | dq_no_data);
          ++stats.no_data_pixels;
        }

        bool low_rejected = false;
        if (low_rejection_map.present) {
          const float low = low_rejection_map.value(index);
          update_finite_nonnegative_count_stats(stats.low_rejection, low);
          low_rejected = low > 0.0f;
          if (low_rejected) {
            flags = static_cast<std::int16_t>(flags | dq_low_rejected);
            ++stats.low_rejected_pixels;
          }
        }

        bool high_rejected = false;
        if (high_rejection_map.present) {
          const float high = high_rejection_map.value(index);
          update_finite_nonnegative_count_stats(stats.high_rejection, high);
          high_rejected = high > 0.0f;
          if (high_rejected) {
            flags = static_cast<std::int16_t>(flags | dq_high_rejected);
            ++stats.high_rejected_pixels;
          }
        }

        if (low_rejected || high_rejected) {
          ++stats.rejection_reduced_pixels;
        }
        if ((flags & dq_warp_edge) != 0) {
          ++stats.warp_edge_pixels;
        }
        if (flags == 0) {
          ++stats.valid_pixels;
        }
        dq_data[index] = flags;
      }
    };

    if (thread_count == 1) {
      scan_range(0, total_pixels, loop_stats);
    } else {
      std::vector<HostDqMapStats> local_stats(thread_count);
      std::vector<std::thread> workers;
      workers.reserve(thread_count);
      for (std::size_t thread_index = 0; thread_index < thread_count; ++thread_index) {
        const std::size_t begin = (total_pixels * thread_index) / thread_count;
        const std::size_t end = (total_pixels * (thread_index + 1u)) / thread_count;
        workers.emplace_back([&, begin, end, thread_index]() {
          scan_range(begin, end, local_stats[thread_index]);
        });
      }
      for (auto& worker : workers) {
        worker.join();
      }
      for (const auto& stats : local_stats) {
        merge_dq_map_stats(loop_stats, stats);
      }
    }
  }

  py::dict summary;
  summary["valid"] = loop_stats.valid_pixels;
  if (loop_stats.no_data_pixels != 0) {
    summary["no_data"] = loop_stats.no_data_pixels;
  }
  if (loop_stats.warp_edge_pixels != 0) {
    summary["warp_edge"] = loop_stats.warp_edge_pixels;
  }
  if (loop_stats.low_rejected_pixels != 0) {
    summary["low_rejected"] = loop_stats.low_rejected_pixels;
  }
  if (loop_stats.high_rejected_pixels != 0) {
    summary["high_rejected"] = loop_stats.high_rejected_pixels;
  }

  py::dict stats;
  stats["schema_version"] = 1;
  stats["stats_source"] = "resident_dq_map_single_pass";
  stats["stats_backend"] = "native_host_fast_count_maps";
  stats["stats_profile"] = "resident_valid_master_nonnegative_count_map_native_i16";
  stats["native_method"] = "resident_dq_map_count_maps_i16";
  stats["native_thread_count"] = static_cast<int>(thread_count);
  py::dict input_dtypes;
  input_dtypes["coverage"] =
      coverage_map.present ? py::object(py::str(coverage_map.dtype_name)) : py::none();
  input_dtypes["low_rejection"] =
      low_rejection_map.present ? py::object(py::str(low_rejection_map.dtype_name)) : py::none();
  input_dtypes["high_rejection"] =
      high_rejection_map.present ? py::object(py::str(high_rejection_map.dtype_name)) : py::none();
  input_dtypes["geometric_warp_coverage"] =
      geometric_warp_coverage_map.present
          ? py::object(py::str(geometric_warp_coverage_map.dtype_name))
          : py::none();
  stats["count_map_input_dtypes"] = input_dtypes;
  stats["post_rejection_coverage"] =
      coverage_map.present ? py::object(coverage_stats_to_dict(loop_stats.post_rejection_coverage)) : py::none();
  stats["post_rejection_zero_pixels"] =
      coverage_map.present ? py::object(py::int_(loop_stats.post_rejection_zero_pixels)) : py::none();
  stats["geometric_warp_coverage"] =
      geometric_warp_coverage_map.present
          ? py::object(coverage_stats_to_dict(loop_stats.geometric_warp_coverage))
          : py::none();
  stats["geometric_zero_pixels"] =
      geometric_warp_coverage_map.present ? py::object(py::int_(loop_stats.geometric_zero_pixels)) : py::none();
  stats["geometric_partial_pixels"] =
      geometric_warp_coverage_map.present ? py::object(py::int_(loop_stats.geometric_partial_pixels)) : py::none();
  stats["geometric_full_pixels"] =
      geometric_warp_coverage_map.present ? py::object(py::int_(loop_stats.geometric_full_pixels)) : py::none();
  stats["low_rejection"] =
      low_rejection_map.present
          ? py::object(
                finite_nonnegative_count_map_stats_to_dict(
                    loop_stats.low_rejection,
                    master.height,
                    master.width,
                    low_rejection_map.dtype_name))
          : py::object(absent_count_map_stats());
  stats["high_rejection"] =
      high_rejection_map.present
          ? py::object(
                finite_nonnegative_count_map_stats_to_dict(
                    loop_stats.high_rejection,
                    master.height,
                    master.width,
                    high_rejection_map.dtype_name))
          : py::object(absent_count_map_stats());
  if (low_rejection_map.present && high_rejection_map.present) {
    stats["rejection_reduced_pixels"] = loop_stats.rejection_reduced_pixels;
    stats["rejection_reduced_pixels_source"] = "low_high_rejection_masks";
  } else if (low_rejection_map.present) {
    stats["rejection_reduced_pixels"] = loop_stats.low_rejected_pixels;
    stats["rejection_reduced_pixels_source"] = "low_rejection_mask";
  } else if (high_rejection_map.present) {
    stats["rejection_reduced_pixels"] = loop_stats.high_rejected_pixels;
    stats["rejection_reduced_pixels_source"] = "high_rejection_mask";
  } else {
    stats["rejection_reduced_pixels"] = py::none();
    stats["rejection_reduced_pixels_source"] = "unavailable";
  }
  return py::make_tuple(dq, summary, stats);
}

py::tuple resident_dq_map_host_f32(
    py::object master_obj,
    py::object weight_map_obj,
    py::object coverage_map_obj,
    py::object low_rejection_map_obj,
    py::object high_rejection_map_obj,
    py::object geometric_warp_coverage_map_obj,
    int active_frame_count) {
  const HostFloat2D master = require_host_float2d(master_obj, "master");
  const HostFloat2D weight_map = require_host_float2d(weight_map_obj, "weight_map");
  const HostFloat2D coverage_map = optional_host_float2d(coverage_map_obj, "coverage_map");
  const HostFloat2D low_rejection_map = optional_host_float2d(low_rejection_map_obj, "low_rejection_map");
  const HostFloat2D high_rejection_map = optional_host_float2d(high_rejection_map_obj, "high_rejection_map");
  const HostFloat2D geometric_warp_coverage_map =
      optional_host_float2d(geometric_warp_coverage_map_obj, "geometric_warp_coverage_map");
  require_same_shape(weight_map, master, "weight_map");
  require_same_shape(coverage_map, master, "coverage_map");
  require_same_shape(low_rejection_map, master, "low_rejection_map");
  require_same_shape(high_rejection_map, master, "high_rejection_map");
  require_same_shape(geometric_warp_coverage_map, master, "geometric_warp_coverage_map");

  constexpr std::uint32_t dq_no_data = 1u << 0;
  constexpr std::uint32_t dq_warp_edge = 1u << 6;
  constexpr std::uint32_t dq_low_rejected = 1u << 8;
  constexpr std::uint32_t dq_high_rejected = 1u << 9;
  const std::size_t total_pixels =
      static_cast<std::size_t>(master.height) * static_cast<std::size_t>(master.width);
  py::array_t<std::uint32_t> dq({master.height, master.width});
  const py::buffer_info dq_info = dq.request();
  auto* dq_data = static_cast<std::uint32_t*>(dq_info.ptr);
  HostDqMapStats loop_stats;
  const int expected_count = active_frame_count > 0 ? active_frame_count : 0;

  {
    py::gil_scoped_release release;
    for (std::size_t index = 0; index < total_pixels; ++index) {
      std::uint32_t flags = 0;
      const float master_value = master.data[index];
      const float weight_value = weight_map.data[index];
      bool invalid = !std::isfinite(master_value) || !std::isfinite(weight_value) || weight_value <= 0.0f;

      if (coverage_map.present) {
        const float coverage = coverage_map.data[index];
        update_coverage_stats(loop_stats.post_rejection_coverage, coverage);
        const bool coverage_finite = std::isfinite(coverage);
        if (!coverage_finite || coverage <= 0.5f) {
          invalid = true;
          flags |= dq_warp_edge;
          if (coverage_finite) {
            ++loop_stats.post_rejection_zero_pixels;
          }
        }
      }

      if (geometric_warp_coverage_map.present) {
        const float geometric = geometric_warp_coverage_map.data[index];
        update_coverage_stats(loop_stats.geometric_warp_coverage, geometric);
        const bool geometric_finite = std::isfinite(geometric);
        if (!geometric_finite || geometric <= 0.5f) {
          invalid = true;
          flags |= dq_warp_edge;
          if (geometric_finite) {
            ++loop_stats.geometric_zero_pixels;
          }
        }
        if (expected_count > 0 && geometric_finite && geometric > 0.5f) {
          if (geometric < static_cast<float>(expected_count) - 0.5f) {
            flags |= dq_warp_edge;
            ++loop_stats.geometric_partial_pixels;
          } else {
            ++loop_stats.geometric_full_pixels;
          }
        }
      }

      if (invalid) {
        flags |= dq_no_data;
        ++loop_stats.no_data_pixels;
      }

      bool low_rejected = false;
      if (low_rejection_map.present) {
        const float low = low_rejection_map.data[index];
        update_count_map_stats(loop_stats.low_rejection, low);
        low_rejected = std::isfinite(low) && low > 0.0f;
        if (low_rejected) {
          flags |= dq_low_rejected;
          ++loop_stats.low_rejected_pixels;
        }
      }

      bool high_rejected = false;
      if (high_rejection_map.present) {
        const float high = high_rejection_map.data[index];
        update_count_map_stats(loop_stats.high_rejection, high);
        high_rejected = std::isfinite(high) && high > 0.0f;
        if (high_rejected) {
          flags |= dq_high_rejected;
          ++loop_stats.high_rejected_pixels;
        }
      }

      if (low_rejected || high_rejected) {
        ++loop_stats.rejection_reduced_pixels;
      }
      if ((flags & dq_warp_edge) != 0) {
        ++loop_stats.warp_edge_pixels;
      }
      if (flags == 0) {
        ++loop_stats.valid_pixels;
      }
      dq_data[index] = flags;
    }
  }

  py::dict summary;
  summary["valid"] = loop_stats.valid_pixels;
  if (loop_stats.no_data_pixels != 0) {
    summary["no_data"] = loop_stats.no_data_pixels;
  }
  if (loop_stats.warp_edge_pixels != 0) {
    summary["warp_edge"] = loop_stats.warp_edge_pixels;
  }
  if (loop_stats.low_rejected_pixels != 0) {
    summary["low_rejected"] = loop_stats.low_rejected_pixels;
  }
  if (loop_stats.high_rejected_pixels != 0) {
    summary["high_rejected"] = loop_stats.high_rejected_pixels;
  }

  py::dict stats;
  stats["schema_version"] = 1;
  stats["stats_source"] = "resident_dq_map_single_pass";
  stats["stats_backend"] = "native_host";
  stats["stats_profile"] = "resident_dq_map_host_single_pass";
  stats["native_method"] = "resident_dq_map_host_f32";
  stats["post_rejection_coverage"] =
      coverage_map.present ? py::object(coverage_stats_to_dict(loop_stats.post_rejection_coverage)) : py::none();
  stats["post_rejection_zero_pixels"] =
      coverage_map.present ? py::object(py::int_(loop_stats.post_rejection_zero_pixels)) : py::none();
  stats["geometric_warp_coverage"] =
      geometric_warp_coverage_map.present
          ? py::object(coverage_stats_to_dict(loop_stats.geometric_warp_coverage))
          : py::none();
  stats["geometric_zero_pixels"] =
      geometric_warp_coverage_map.present ? py::object(py::int_(loop_stats.geometric_zero_pixels)) : py::none();
  stats["geometric_partial_pixels"] =
      geometric_warp_coverage_map.present ? py::object(py::int_(loop_stats.geometric_partial_pixels)) : py::none();
  stats["geometric_full_pixels"] =
      geometric_warp_coverage_map.present ? py::object(py::int_(loop_stats.geometric_full_pixels)) : py::none();
  stats["low_rejection"] =
      low_rejection_map.present
          ? py::object(count_map_stats_to_dict(loop_stats.low_rejection, master.height, master.width))
          : py::object(absent_count_map_stats());
  stats["high_rejection"] =
      high_rejection_map.present
          ? py::object(count_map_stats_to_dict(loop_stats.high_rejection, master.height, master.width))
          : py::object(absent_count_map_stats());
  if (low_rejection_map.present && high_rejection_map.present) {
    stats["rejection_reduced_pixels"] = loop_stats.rejection_reduced_pixels;
    stats["rejection_reduced_pixels_source"] = "low_high_rejection_masks";
  } else if (low_rejection_map.present) {
    stats["rejection_reduced_pixels"] = loop_stats.low_rejected_pixels;
    stats["rejection_reduced_pixels_source"] = "low_rejection_mask";
  } else if (high_rejection_map.present) {
    stats["rejection_reduced_pixels"] = loop_stats.high_rejected_pixels;
    stats["rejection_reduced_pixels_source"] = "high_rejection_mask";
  } else {
    stats["rejection_reduced_pixels"] = py::none();
    stats["rejection_reduced_pixels_source"] = "unavailable";
  }
  return py::make_tuple(dq, summary, stats);
}

bool resident_dq_map_host_f32_optimized() {
#ifdef NDEBUG
  return true;
#else
  return false;
#endif
}

PYBIND11_MODULE(_glass_cuda_native, m) {
  m.doc() = "Native CUDA backend for GLASS";
  m.def("cuda_available", &cuda_available);
  m.def("list_devices", &list_devices);
  m.def("get_device_info", &get_device_info);
  m.def("host_pinned_empty_f32", &host_pinned_empty_f32, py::arg("height"), py::arg("width"));
  m.def("host_pinned_empty_u8", &host_pinned_empty_u8, py::arg("byte_count"));
  m.def(
      "read_simple_fits_into_f32",
      &read_simple_fits_into_f32,
      py::arg("path"),
      py::arg("data_offset"),
      py::arg("height"),
      py::arg("width"),
      py::arg("bitpix"),
      py::arg("bscale"),
      py::arg("bzero"),
      py::arg("blank"),
      py::arg("output"));
  m.def(
      "read_simple_fits_raw_into_u8",
      &read_simple_fits_raw_into_u8,
      py::arg("path"),
      py::arg("data_offset"),
      py::arg("byte_count"),
      py::arg("output"));
  m.def(
      "read_simple_fits_raw_batch_into_u8",
      &read_simple_fits_raw_batch_into_u8,
      py::arg("paths"),
      py::arg("data_offsets"),
      py::arg("byte_counts"),
      py::arg("outputs"),
      py::arg("max_workers") = 0);
  py::class_<RawFitsReadQueue>(m, "RawFitsReadQueue")
      .def(py::init<int>(), py::arg("worker_count") = 1)
      .def(
          "submit",
          &RawFitsReadQueue::submit,
          py::arg("frame_index"),
          py::arg("path"),
          py::arg("data_offset"),
          py::arg("byte_count"),
          py::arg("output"))
      .def("wait_completed", &RawFitsReadQueue::wait_completed, py::arg("timeout_s") = -1.0)
      .def("stats", &RawFitsReadQueue::stats)
      .def("close", &RawFitsReadQueue::close);
  m.def("smoke_add_f32", &smoke_add_f32);
  m.def("reduce_mean_tile_f32", &reduce_mean_tile_f32);
  m.def("calibrate_tile_f32", &calibrate_tile_f32);
  m.def("mean_stack_tiles_f32", &mean_stack_tiles_f32);
  m.def("warp_translation_f32", &warp_translation_f32);
  m.def("warp_translation_bilinear_f32", &warp_translation_bilinear_f32);
  m.def("warp_matrix_bilinear_f32", &warp_matrix_bilinear_f32);
  m.def(
      "warp_matrix_lanczos3_f32",
      &warp_matrix_lanczos3_f32,
      py::arg("input"),
      py::arg("matrix"),
      py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
      py::arg("clamping_threshold") = -1.0f);
  m.def(
      "matrix_alignment_metrics_f32",
      &matrix_alignment_metrics_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("matrix"),
      py::arg("sample_stride") = 1);
  m.def(
      "refine_matrix_translation_with_metrics_f32",
      &refine_matrix_translation_with_metrics_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("matrix"),
      py::arg("search_radius_px") = 1.0f,
      py::arg("coarse_step_px") = 0.25f,
      py::arg("fine_radius_px") = 0.25f,
      py::arg("fine_step_px") = 0.0625f,
      py::arg("coarse_sample_stride") = 4,
      py::arg("final_sample_stride") = 1);
  m.def(
      "refine_matrix_translation_candidates_with_metrics_f32",
      &refine_matrix_translation_candidates_with_metrics_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("matrices"),
      py::arg("search_radius_px") = 1.0f,
      py::arg("coarse_step_px") = 0.25f,
      py::arg("fine_radius_px") = 0.25f,
      py::arg("fine_step_px") = 0.0625f,
      py::arg("coarse_sample_stride") = 4,
      py::arg("final_sample_stride") = 1);
  m.def(
      "estimate_translation_search_f32",
      &estimate_translation_search_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("max_shift_x"),
      py::arg("max_shift_y"),
      py::arg("sample_stride") = 1);
  m.def(
      "estimate_translation_subpixel_ncc_f32",
      &estimate_translation_subpixel_ncc_f32,
      py::arg("reference"),
      py::arg("moving"),
      py::arg("center_dx"),
      py::arg("center_dy"),
      py::arg("radius_steps"),
      py::arg("step"),
      py::arg("sample_stride") = 1);
  m.def(
      "estimate_translation_from_catalogs_f32",
      &estimate_translation_from_catalogs_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"),
      py::arg("tolerance_px") = 1.0f,
      py::arg("max_abs_dx") = -1.0f,
      py::arg("max_abs_dy") = -1.0f,
      py::arg("prior_dx") = 0.0f,
      py::arg("prior_dy") = 0.0f,
      py::arg("prior_radius_px") = -1.0f);
  m.def(
      "estimate_similarity_from_pairs_f32",
      &estimate_similarity_from_pairs_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"));
  m.def(
      "triangle_asterism_descriptors_f32",
      &triangle_asterism_descriptors_f32,
      py::arg("x"),
      py::arg("y"),
      py::arg("max_stars") = 80,
      py::arg("neighbors") = 5,
      py::arg("max_descriptors") = 1200);
  m.def(
      "triangle_asterism_descriptors_batch_f32",
      &triangle_asterism_descriptors_batch_f32,
      py::arg("x_list"),
      py::arg("y_list"),
      py::arg("max_stars") = 80,
      py::arg("neighbors") = 5,
      py::arg("max_descriptors") = 1200);
  m.def(
      "estimate_similarity_from_triangle_descriptors_f32",
      &estimate_similarity_from_triangle_descriptors_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"),
      py::arg("reference_descriptors"),
      py::arg("reference_indices"),
      py::arg("moving_descriptors"),
      py::arg("moving_indices"),
      py::arg("tolerance_px") = 2.0f,
      py::arg("descriptor_radius") = 0.1f);
  m.def(
      "estimate_similarity_from_triangle_descriptors_batch_f32",
      &estimate_similarity_from_triangle_descriptors_batch_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("reference_descriptors"),
      py::arg("reference_indices"),
      py::arg("moving_x_list"),
      py::arg("moving_y_list"),
      py::arg("moving_descriptors_list"),
      py::arg("moving_indices_list"),
      py::arg("tolerance_px") = 2.0f,
      py::arg("descriptor_radius") = 0.1f);
  m.def(
      "estimate_similarity_from_catalogs_f32",
      &estimate_similarity_from_catalogs_f32,
      py::arg("reference_x"),
      py::arg("reference_y"),
      py::arg("moving_x"),
      py::arg("moving_y"),
      py::arg("tolerance_px") = 2.0f,
      py::arg("min_pair_distance") = 2.0f,
      py::arg("prior_dx") = 0.0f,
      py::arg("prior_dy") = 0.0f,
      py::arg("prior_radius_px") = -1.0f,
      py::arg("min_scale") = 0.0f,
      py::arg("max_scale") = std::numeric_limits<float>::max(),
      py::arg("max_abs_rotation_rad") = -1.0f,
      py::arg("top_k") = 0);
  m.def("local_norm_apply_f32", &local_norm_apply_f32);
  m.def(
      "local_norm_apply_grid_f32",
      &local_norm_apply_grid_f32,
      py::arg("input"),
      py::arg("scales"),
      py::arg("offsets"),
      py::arg("tile_height"),
      py::arg("tile_width"));
  m.def("local_norm_pair_stats_f32", &local_norm_pair_stats_f32);
  m.def("integrate_accumulate_mean_tile_f32", &integrate_accumulate_mean_tile_f32);
  m.def("star_local_max_mask_f32", &star_local_max_mask_f32);
  m.def("star_candidates_f32", &star_candidates_f32);
  m.def("star_top_candidates_f32", &star_top_candidates_f32);
  m.def(
      "star_top_nms_candidates_f32",
      &star_top_nms_candidates_f32,
      py::arg("input"),
      py::arg("threshold"),
      py::arg("scan_candidates"),
      py::arg("max_output_candidates"),
      py::arg("min_separation_px"));
  m.def(
      "star_grid_top_nms_candidates_f32",
      &star_grid_top_nms_candidates_f32,
      py::arg("input"),
      py::arg("threshold"),
      py::arg("grid_cols"),
      py::arg("grid_rows"),
      py::arg("candidates_per_cell"),
      py::arg("max_output_candidates"),
      py::arg("min_separation_px"));
  m.def("star_grid_candidates_f32", &star_grid_candidates_f32);
  m.def(
      "resident_dq_map_host_f32",
      &resident_dq_map_host_f32,
      py::arg("master"),
      py::arg("weight_map"),
      py::arg("coverage_map"),
      py::arg("low_rejection_map"),
      py::arg("high_rejection_map"),
      py::arg("geometric_warp_coverage_map") = py::none(),
      py::arg("active_frame_count") = 0);
  m.def(
      "resident_dq_map_count_maps_i16",
      &resident_dq_map_count_maps_i16,
      py::arg("master"),
      py::arg("coverage_map"),
      py::arg("low_rejection_map"),
      py::arg("high_rejection_map"),
      py::arg("geometric_warp_coverage_map") = py::none(),
      py::arg("active_frame_count") = 0);
  m.def("resident_dq_map_host_f32_optimized", &resident_dq_map_host_f32_optimized);
  py::class_<ResidentCalibratedStack>(m, "ResidentCalibratedStack")
      .def(py::init<std::size_t, std::size_t, std::size_t>())
      .def_property_readonly("frame_count", &ResidentCalibratedStack::frame_count)
      .def_property_readonly("height", &ResidentCalibratedStack::height)
      .def_property_readonly("width", &ResidentCalibratedStack::width)
      .def_property_readonly("pixels_per_frame", &ResidentCalibratedStack::pixels_per_frame)
      .def_property_readonly("loaded_count", &ResidentCalibratedStack::loaded_count)
      .def_property_readonly("host_pinned_bytes", &ResidentCalibratedStack::host_pinned_bytes)
      .def_property_readonly("calibration_lane_count", &ResidentCalibratedStack::calibration_lane_count)
      .def_property_readonly(
          "calibration_lane_buffer_bytes",
          &ResidentCalibratedStack::calibration_lane_buffer_bytes)
      .def_property_readonly("warp_scratch_bytes", &ResidentCalibratedStack::warp_scratch_bytes)
      .def_property_readonly("warp_copy_mode", &ResidentCalibratedStack::warp_copy_mode)
      .def_property_readonly("bytes_allocated", &ResidentCalibratedStack::bytes_allocated)
      .def_property_readonly("warp_coverage_frame_count", &ResidentCalibratedStack::warp_coverage_frame_count)
      .def(
          "set_calibration_masters",
          &ResidentCalibratedStack::set_calibration_masters,
          py::arg("bias") = py::none(),
          py::arg("dark") = py::none(),
          py::arg("flat") = py::none())
      .def("reset_warp_coverage", &ResidentCalibratedStack::reset_warp_coverage)
      .def("accumulate_full_warp_coverage_frame", &ResidentCalibratedStack::accumulate_full_warp_coverage_frame)
      .def("warp_coverage_map", &ResidentCalibratedStack::warp_coverage_map)
      .def(
          "download_frame_tile",
          &ResidentCalibratedStack::download_frame_tile,
          py::arg("index"),
          py::arg("x0"),
          py::arg("y0"),
          py::arg("x1"),
          py::arg("y1"))
      .def(
          "download_frames_tile",
          &ResidentCalibratedStack::download_frames_tile,
          py::arg("indices"),
          py::arg("x0"),
          py::arg("y0"),
          py::arg("x1"),
          py::arg("y1"))
      .def("upload_calibrated_frame", &ResidentCalibratedStack::upload_calibrated_frame)
      .def(
          "apply_invalid_mask_frame",
          &ResidentCalibratedStack::apply_invalid_mask_frame,
          py::arg("index"),
          py::arg("invalid_mask"))
      .def(
          "apply_cosmetic_threshold_mask_frame",
          &ResidentCalibratedStack::apply_cosmetic_threshold_mask_frame,
          py::arg("index"),
          py::arg("low_threshold"),
          py::arg("high_threshold"))
      .def(
          "count_cosmetic_threshold_mask_frame",
          &ResidentCalibratedStack::count_cosmetic_threshold_mask_frame,
          py::arg("index"),
          py::arg("low_threshold"),
          py::arg("high_threshold"))
      .def(
          "apply_cosmetic_threshold_mask_frames",
          &ResidentCalibratedStack::apply_cosmetic_threshold_mask_frames,
          py::arg("indices"),
          py::arg("low_thresholds"),
          py::arg("high_thresholds"))
      .def(
          "count_cosmetic_threshold_mask_frames",
          &ResidentCalibratedStack::count_cosmetic_threshold_mask_frames,
          py::arg("indices"),
          py::arg("low_thresholds"),
          py::arg("high_thresholds"))
      .def(
          "apply_isolated_cosmetic_threshold_mask_frame",
          &ResidentCalibratedStack::apply_isolated_cosmetic_threshold_mask_frame,
          py::arg("index"),
          py::arg("low_threshold"),
          py::arg("high_threshold"),
          py::arg("median"),
          py::arg("sigma"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "count_isolated_cosmetic_threshold_mask_frame",
          &ResidentCalibratedStack::count_isolated_cosmetic_threshold_mask_frame,
          py::arg("index"),
          py::arg("low_threshold"),
          py::arg("high_threshold"),
          py::arg("median"),
          py::arg("sigma"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "apply_star_protected_isolated_cosmetic_threshold_mask_frame",
          &ResidentCalibratedStack::apply_star_protected_isolated_cosmetic_threshold_mask_frame,
          py::arg("index"),
          py::arg("low_threshold"),
          py::arg("high_threshold"),
          py::arg("median"),
          py::arg("sigma"),
          py::arg("star_xs"),
          py::arg("star_ys"),
          py::arg("star_protection_radius"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "count_star_protected_isolated_cosmetic_threshold_mask_frame",
          &ResidentCalibratedStack::count_star_protected_isolated_cosmetic_threshold_mask_frame,
          py::arg("index"),
          py::arg("low_threshold"),
          py::arg("high_threshold"),
          py::arg("median"),
          py::arg("sigma"),
          py::arg("star_xs"),
          py::arg("star_ys"),
          py::arg("star_protection_radius"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "apply_star_protected_isolated_cosmetic_threshold_mask_frames",
          &ResidentCalibratedStack::apply_star_protected_isolated_cosmetic_threshold_mask_frames,
          py::arg("indices"),
          py::arg("low_thresholds"),
          py::arg("high_thresholds"),
          py::arg("medians"),
          py::arg("sigmas"),
          py::arg("star_xs_flat"),
          py::arg("star_ys_flat"),
          py::arg("star_offsets"),
          py::arg("star_counts"),
          py::arg("star_protection_radii"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "count_star_protected_isolated_cosmetic_threshold_mask_frames",
          &ResidentCalibratedStack::count_star_protected_isolated_cosmetic_threshold_mask_frames,
          py::arg("indices"),
          py::arg("low_thresholds"),
          py::arg("high_thresholds"),
          py::arg("medians"),
          py::arg("sigmas"),
          py::arg("star_xs_flat"),
          py::arg("star_ys_flat"),
          py::arg("star_offsets"),
          py::arg("star_counts"),
          py::arg("star_protection_radii"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "apply_isolated_cosmetic_threshold_mask_frames",
          &ResidentCalibratedStack::apply_isolated_cosmetic_threshold_mask_frames,
          py::arg("indices"),
          py::arg("low_thresholds"),
          py::arg("high_thresholds"),
          py::arg("medians"),
          py::arg("sigmas"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "count_isolated_cosmetic_threshold_mask_frames",
          &ResidentCalibratedStack::count_isolated_cosmetic_threshold_mask_frames,
          py::arg("indices"),
          py::arg("low_thresholds"),
          py::arg("high_thresholds"),
          py::arg("medians"),
          py::arg("sigmas"),
          py::arg("structure_sigma") = 1.5f,
          py::arg("min_neighbor_support") = 2)
      .def(
          "frame_sampled_robust_stats",
          &ResidentCalibratedStack::frame_sampled_robust_stats,
          py::arg("index"),
          py::arg("sample_limit") = 65536,
          py::arg("hot_sigma") = 8.0f,
          py::arg("cold_sigma") = 8.0f)
      .def(
          "frame_histogram_robust_stats",
          &ResidentCalibratedStack::frame_histogram_robust_stats,
          py::arg("index"),
          py::arg("bin_count") = 4096,
          py::arg("hot_sigma") = 8.0f,
          py::arg("cold_sigma") = 8.0f)
      .def(
          "frames_histogram_robust_stats",
          &ResidentCalibratedStack::frames_histogram_robust_stats,
          py::arg("indices"),
          py::arg("bin_count") = 4096,
          py::arg("hot_sigma") = 8.0f,
          py::arg("cold_sigma") = 8.0f)
      .def(
          "calibrate_frame",
          &ResidentCalibratedStack::calibrate_frame,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_timed",
          &ResidentCalibratedStack::calibrate_frame_timed,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_pinned_async",
          &ResidentCalibratedStack::calibrate_frame_pinned_async,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_pinned_async_timed",
          &ResidentCalibratedStack::calibrate_frame_pinned_async_timed,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frame_host_async_timed",
          &ResidentCalibratedStack::calibrate_frame_host_async_timed,
          py::arg("index"),
          py::arg("light"),
          py::arg("light_exposure_s"),
          py::arg("dark_exposure_s") = py::none(),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_host_async_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_host_async_multistream_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_multistream_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_host_async_multistream_h2d_release_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_multistream_h2d_release_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("policy") = py::none())
      .def(
          "finish_pending_calibration_timed",
          &ResidentCalibratedStack::finish_pending_calibration_timed)
      .def(
          "calibrate_frames_host_async_multistream_callback_release_timed",
          &ResidentCalibratedStack::calibrate_frames_host_async_multistream_callback_release_timed,
          py::arg("indices"),
          py::arg("lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("wave_frames"),
          py::arg("release_callback"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed",
          &ResidentCalibratedStack::calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed,
          py::arg("indices"),
          py::arg("raw_lights"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("wave_frames"),
          py::arg("release_callback"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_fits_u16be_bzero_paths_multistream_timed",
          &ResidentCalibratedStack::calibrate_frames_fits_u16be_bzero_paths_multistream_timed,
          py::arg("indices"),
          py::arg("paths"),
          py::arg("data_offsets"),
          py::arg("byte_counts"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("wave_frames"),
          py::arg("policy") = py::none())
      .def(
          "calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed",
          &ResidentCalibratedStack::calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed,
          py::arg("indices"),
          py::arg("paths"),
          py::arg("data_offsets"),
          py::arg("byte_counts"),
          py::arg("light_exposures"),
          py::arg("dark_exposures"),
          py::arg("stream_count"),
          py::arg("queue_buffer_count"),
          py::arg("worker_count"),
          py::arg("policy") = py::none())
      .def(
          "apply_translation_frame",
          &ResidentCalibratedStack::apply_translation_frame,
          py::arg("index"),
          py::arg("dx"),
          py::arg("dy"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_translation_bilinear_frame",
          &ResidentCalibratedStack::apply_translation_bilinear_frame,
          py::arg("index"),
          py::arg("dx"),
          py::arg("dy"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_matrix_bilinear_frame",
          &ResidentCalibratedStack::apply_matrix_bilinear_frame,
          py::arg("index"),
          py::arg("matrix"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN())
      .def(
          "apply_matrix_lanczos3_frame",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frame,
          py::arg("index"),
          py::arg("matrix"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f)
      .def(
          "apply_matrix_bilinear_frames",
          &ResidentCalibratedStack::apply_matrix_bilinear_frames,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("max_chunk_capacity_frames") = 0,
          py::arg("track_coverage") = true)
      .def(
          "apply_matrix_bilinear_frames_pipelined",
          &ResidentCalibratedStack::apply_matrix_bilinear_frames_pipelined,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("max_chunk_capacity_frames") = 0,
          py::arg("track_coverage") = true,
          py::arg("stream_count") = 2)
      .def(
          "apply_matrix_bilinear_frames_loop",
          &ResidentCalibratedStack::apply_matrix_bilinear_frames_loop,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("track_coverage") = true)
      .def(
          "apply_matrix_lanczos3_frames",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frames,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f,
          py::arg("max_chunk_capacity_frames") = 0,
          py::arg("track_coverage") = true)
      .def(
          "apply_matrix_lanczos3_frames_pipelined",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frames_pipelined,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f,
          py::arg("max_chunk_capacity_frames") = 0,
          py::arg("track_coverage") = true,
          py::arg("stream_count") = 2)
      .def(
          "apply_matrix_lanczos3_frames_loop",
          &ResidentCalibratedStack::apply_matrix_lanczos3_frames_loop,
          py::arg("indices"),
          py::arg("matrices"),
          py::arg("fill") = std::numeric_limits<float>::quiet_NaN(),
          py::arg("clamping_threshold") = -1.0f,
          py::arg("track_coverage") = true)
      .def(
          "matrix_alignment_metrics_to_reference",
          &ResidentCalibratedStack::matrix_alignment_metrics_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("matrix"),
          py::arg("sample_stride") = 1)
      .def(
          "star_core_metrics_candidates_to_reference",
          &ResidentCalibratedStack::star_core_metrics_candidates_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("matrices"),
          py::arg("threshold"))
      .def(
          "refine_matrix_translation_candidates_to_reference",
          &ResidentCalibratedStack::refine_matrix_translation_candidates_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("matrices"),
          py::arg("search_radius_px") = 1.0f,
          py::arg("coarse_step_px") = 0.25f,
          py::arg("fine_radius_px") = 0.25f,
          py::arg("fine_step_px") = 0.0625f,
          py::arg("coarse_sample_stride") = 4,
          py::arg("final_sample_stride") = 1)
      .def(
          "refine_matrix_translation_candidates_batch_to_reference",
          &ResidentCalibratedStack::refine_matrix_translation_candidates_batch_to_reference,
          py::arg("reference_index"),
          py::arg("moving_indices"),
          py::arg("matrices"),
          py::arg("search_radius_px") = 1.0f,
          py::arg("coarse_step_px") = 0.25f,
          py::arg("fine_radius_px") = 0.25f,
          py::arg("fine_step_px") = 0.0625f,
          py::arg("coarse_sample_stride") = 4,
          py::arg("final_sample_stride") = 1)
      .def(
          "estimate_translation_to_reference",
          &ResidentCalibratedStack::estimate_translation_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("max_shift_x"),
          py::arg("max_shift_y"),
          py::arg("sample_stride") = 1)
      .def(
          "estimate_translation_subpixel_to_reference",
          &ResidentCalibratedStack::estimate_translation_subpixel_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("center_dx"),
          py::arg("center_dy"),
          py::arg("radius_steps"),
          py::arg("step"),
          py::arg("sample_stride") = 1)
      .def("frame_global_stats", &ResidentCalibratedStack::frame_global_stats)
      .def(
          "frame_pair_grid_stats",
          &ResidentCalibratedStack::frame_pair_grid_stats,
          py::arg("reference_index"),
          py::arg("source_index"),
          py::arg("tile_height"),
          py::arg("tile_width"))
      .def(
          "frame_pair_grid_stats_batch",
          &ResidentCalibratedStack::frame_pair_grid_stats_batch,
          py::arg("reference_index"),
          py::arg("source_indices"),
          py::arg("tile_height"),
          py::arg("tile_width"))
      .def(
          "apply_global_normalization_frame",
          &ResidentCalibratedStack::apply_global_normalization_frame,
          py::arg("index"),
          py::arg("scale"),
          py::arg("offset"))
      .def(
          "apply_grid_normalization_frame",
          &ResidentCalibratedStack::apply_grid_normalization_frame,
          py::arg("index"),
          py::arg("scales"),
          py::arg("offsets"),
          py::arg("tile_height"),
          py::arg("tile_width"))
      .def(
          "apply_grid_normalization_frames",
          &ResidentCalibratedStack::apply_grid_normalization_frames,
          py::arg("frame_indices"),
          py::arg("scales"),
          py::arg("offsets"),
          py::arg("tile_height"),
          py::arg("tile_width"))
      .def("star_local_max_mask", &ResidentCalibratedStack::star_local_max_mask)
      .def("star_candidates", &ResidentCalibratedStack::star_candidates)
      .def("star_top_candidates", &ResidentCalibratedStack::star_top_candidates)
      .def("star_top_nms_candidates", &ResidentCalibratedStack::star_top_nms_candidates)
      .def("star_top_nms_candidates_centroid", &ResidentCalibratedStack::star_top_nms_candidates_centroid)
      .def("star_grid_top_nms_candidates", &ResidentCalibratedStack::star_grid_top_nms_candidates)
      .def("star_grid_top_nms_candidates_centroid", &ResidentCalibratedStack::star_grid_top_nms_candidates_centroid)
      .def(
          "star_grid_top_nms_candidates_deterministic",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_deterministic)
      .def(
          "star_grid_top_nms_candidates_deterministic_centroid",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_deterministic_centroid)
      .def("star_grid_top_nms_candidates_batch", &ResidentCalibratedStack::star_grid_top_nms_candidates_batch)
      .def(
          "star_grid_top_nms_candidates_batch_centroid",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_batch_centroid)
      .def(
          "star_grid_top_nms_candidates_batch_deterministic",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_batch_deterministic)
      .def(
          "star_grid_top_nms_candidates_batch_deterministic_centroid",
          &ResidentCalibratedStack::star_grid_top_nms_candidates_batch_deterministic_centroid)
      .def(
          "estimate_translation_from_stars_to_reference",
          &ResidentCalibratedStack::estimate_translation_from_stars_to_reference,
          py::arg("reference_index"),
          py::arg("moving_index"),
          py::arg("threshold"),
          py::arg("max_candidates"),
          py::arg("tolerance_px"),
          py::arg("max_abs_dx"),
          py::arg("max_abs_dy"),
          py::arg("prior_dx") = 0.0f,
          py::arg("prior_dy") = 0.0f,
          py::arg("prior_radius_px") = -1.0f,
          py::arg("grid_cols") = 0,
          py::arg("grid_rows") = 0)
      .def("integrate_mean", &ResidentCalibratedStack::integrate_mean, py::arg("weights") = py::none())
      .def(
          "integrate_tile_local_mean",
          &ResidentCalibratedStack::integrate_tile_local_mean,
          py::arg("target_mask"),
          py::arg("tile_extents"),
          py::arg("tile_multipliers"),
          py::arg("weights") = py::none())
      .def(
          "integrate_sigma_clip",
          &ResidentCalibratedStack::integrate_sigma_clip,
          py::arg("weights") = py::none(),
          py::arg("low_sigma") = 3.0f,
          py::arg("high_sigma") = 3.0f,
          py::arg("winsorize") = true,
          py::arg("download_mode") = "full")
      .def(
          "integrate_hardened_winsorized_sigma",
          &ResidentCalibratedStack::integrate_hardened_winsorized_sigma,
          py::arg("weights") = py::none(),
          py::arg("low_sigma") = 3.0f,
          py::arg("high_sigma") = 3.0f,
          py::arg("min_samples") = 3,
          py::arg("max_reject_fraction") = 0.5f,
          py::arg("count_map_dtype") = "float32",
          py::arg("profile") = false,
          py::arg("download_mode") = "full")
      .def(
          "integrate_tile_local_sigma_clip",
          &ResidentCalibratedStack::integrate_tile_local_sigma_clip,
          py::arg("target_mask"),
          py::arg("tile_extents"),
          py::arg("tile_multipliers"),
          py::arg("weights") = py::none(),
          py::arg("low_sigma") = 3.0f,
          py::arg("high_sigma") = 3.0f,
          py::arg("winsorize") = true)
      .def(
          "integrate_matrix_warped_mean",
          &ResidentCalibratedStack::integrate_matrix_warped_mean,
          py::arg("matrices"),
          py::arg("weights") = py::none(),
          py::arg("interpolation") = "bilinear",
          py::arg("clamping_threshold") = -1.0f,
          py::arg("download_mode") = "full")
      .def(
          "integrate_matrix_warped_sigma_clip",
          &ResidentCalibratedStack::integrate_matrix_warped_sigma_clip,
          py::arg("matrices"),
          py::arg("weights") = py::none(),
          py::arg("interpolation") = "bilinear",
          py::arg("clamping_threshold") = -1.0f,
          py::arg("low_sigma") = 3.0f,
          py::arg("high_sigma") = 3.0f,
          py::arg("winsorize") = true,
          py::arg("download_mode") = "full");
}
